-- Supabase hardening + audit history
-- Safe to run multiple times.

-- 1) Devices table hardening
ALTER TABLE public.devices
  ALTER COLUMN serial SET NOT NULL,
  ALTER COLUMN device_type SET NOT NULL,
  ALTER COLUMN status SET NOT NULL,
  ALTER COLUMN created_at SET DEFAULT timezone('utc', now()),
  ALTER COLUMN updated_at SET DEFAULT timezone('utc', now());

CREATE UNIQUE INDEX IF NOT EXISTS ux_devices_serial_normalized
  ON public.devices ((upper(regexp_replace(serial, '[^A-Za-z0-9]', '', 'g'))));

CREATE INDEX IF NOT EXISTS ix_devices_status ON public.devices (status);
CREATE INDEX IF NOT EXISTS ix_devices_type ON public.devices (device_type);
CREATE INDEX IF NOT EXISTS ix_devices_updated_at ON public.devices (updated_at DESC);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'devices_status_check'
      AND conrelid = 'public.devices'::regclass
  ) THEN
    ALTER TABLE public.devices
      ADD CONSTRAINT devices_status_check
      CHECK (
        status IN (
          'RECEIVED',
          'PREPARING',
          'PREPARED',
          'SENT',
          'IN_USE',
          'RETURNED',
          'RETIRED'
        )
      ) NOT VALID;
  END IF;
END
$$;

-- 5) Devices RLS split (normal operator vs admin)
ALTER TABLE public.devices ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.is_device_admin()
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
  SELECT
    auth.role() = 'service_role'
    OR lower(coalesce(auth.jwt() -> 'app_metadata' ->> 'device_admin', 'false')) = 'true'
    OR lower(coalesce(auth.jwt() ->> 'device_admin', 'false')) = 'true';
$$;

CREATE OR REPLACE FUNCTION public.guard_device_identity_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NOT public.is_device_admin() THEN
    IF NEW.serial IS DISTINCT FROM OLD.serial
      OR NEW.device_type IS DISTINCT FROM OLD.device_type
      OR NEW.model IS DISTINCT FROM OLD.model THEN
      RAISE EXCEPTION 'Only device_admin can modify serial/device_type/model for existing devices';
    END IF;
  END IF;

  NEW.updated_at = timezone('utc', now());
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_guard_device_identity_update ON public.devices;
CREATE TRIGGER trg_guard_device_identity_update
BEFORE UPDATE ON public.devices
FOR EACH ROW EXECUTE FUNCTION public.guard_device_identity_update();

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'devices'
      AND policyname = 'devices_select_all'
  ) THEN
    CREATE POLICY devices_select_all
      ON public.devices
      FOR SELECT
      TO anon, authenticated
      USING (true);
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'devices'
      AND policyname = 'devices_insert_all'
  ) THEN
    CREATE POLICY devices_insert_all
      ON public.devices
      FOR INSERT
      TO anon, authenticated
      WITH CHECK (
        length(trim(serial)) > 0
        AND status IN ('RECEIVED', 'PREPARING', 'PREPARED', 'SENT', 'IN_USE', 'RETURNED', 'RETIRED')
      );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'devices'
      AND policyname = 'devices_update_all'
  ) THEN
    CREATE POLICY devices_update_all
      ON public.devices
      FOR UPDATE
      TO anon, authenticated
      USING (true)
      WITH CHECK (
        length(trim(serial)) > 0
        AND status IN ('RECEIVED', 'PREPARING', 'PREPARED', 'SENT', 'IN_USE', 'RETURNED', 'RETIRED')
      );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'devices'
      AND policyname = 'devices_delete_admin_only'
  ) THEN
    CREATE POLICY devices_delete_admin_only
      ON public.devices
      FOR DELETE
      TO authenticated
      USING (public.is_device_admin());
  END IF;
END
$$;

-- 2) Audit history table
CREATE TABLE IF NOT EXISTS public.device_audit_log (
  id bigserial PRIMARY KEY,
  event_time timestamptz NOT NULL DEFAULT timezone('utc', now()),
  operation text NOT NULL,
  serial text,
  row_id bigint,
  before_data jsonb,
  after_data jsonb,
  actor text,
  source text NOT NULL DEFAULT 'db_trigger',
  txid bigint NOT NULL DEFAULT txid_current()
);

CREATE INDEX IF NOT EXISTS ix_device_audit_serial ON public.device_audit_log (serial);
CREATE INDEX IF NOT EXISTS ix_device_audit_event_time ON public.device_audit_log (event_time DESC);

-- 3) Trigger-based automatic logging for INSERT / UPDATE / DELETE
CREATE OR REPLACE FUNCTION public.log_device_change()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO public.device_audit_log (operation, serial, row_id, before_data, after_data)
    VALUES ('INSERT', NEW.serial, NEW.id, NULL, to_jsonb(NEW));
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO public.device_audit_log (operation, serial, row_id, before_data, after_data)
    VALUES ('UPDATE', NEW.serial, NEW.id, to_jsonb(OLD), to_jsonb(NEW));
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO public.device_audit_log (operation, serial, row_id, before_data, after_data)
    VALUES ('DELETE', OLD.serial, OLD.id, to_jsonb(OLD), NULL);
    RETURN OLD;
  END IF;

  RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_log_device_change ON public.devices;
CREATE TRIGGER trg_log_device_change
AFTER INSERT OR UPDATE OR DELETE ON public.devices
FOR EACH ROW EXECUTE FUNCTION public.log_device_change();

-- 4) Optional RLS baseline for audit table (read-only with authenticated role)
ALTER TABLE public.device_audit_log ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'device_audit_log'
      AND policyname = 'device_audit_log_read_authenticated'
  ) THEN
    CREATE POLICY device_audit_log_read_authenticated
      ON public.device_audit_log
      FOR SELECT
      TO authenticated
      USING (true);
  END IF;
END
$$;
