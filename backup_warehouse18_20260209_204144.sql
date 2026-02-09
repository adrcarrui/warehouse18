--
-- PostgreSQL database dump
--

\restrict ozhUFiuSfRikadCh8thF5B4skVim1K41p5e6fCWR1Zrm9yvPVQnA83BTF7mx77d

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: consume_from_container(text, numeric, bigint, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.consume_from_container(p_container_code text, p_qty numeric, p_user_id bigint DEFAULT NULL::bigint, p_notes text DEFAULT NULL::text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_container_id BIGINT;
  v_item_id BIGINT;
  v_loc_id BIGINT;
  v_available NUMERIC;
  v_mt_id BIGINT;
  v_movement_id BIGINT;
  v_stock_qty NUMERIC;
BEGIN
  IF p_container_code IS NULL OR length(trim(p_container_code)) = 0 THEN
    RAISE EXCEPTION 'container_code is required';
  END IF;

  IF p_qty IS NULL OR p_qty <= 0 THEN
    RAISE EXCEPTION 'Quantity must be > 0';
  END IF;

  -- Lock container row
  SELECT id, item_id, location_id, quantity
  INTO v_container_id, v_item_id, v_loc_id, v_available
  FROM stock_containers
  WHERE container_code = p_container_code
  FOR UPDATE;

  IF v_container_id IS NULL THEN
    RAISE EXCEPTION 'Container % not found', p_container_code;
  END IF;

  IF v_available < p_qty THEN
    RAISE EXCEPTION 'Not enough quantity in container %. Available=%, requested=%',
      p_container_code, v_available, p_qty;
  END IF;

  -- Ensure GI movement type exists
  SELECT id INTO v_mt_id
  FROM movement_types
  WHERE code = 'GI';

  IF v_mt_id IS NULL THEN
    RAISE EXCEPTION 'movement_types code GI not found. Seed movement_types first.';
  END IF;

  -- Ensure inventory_stock row exists and lock it
  INSERT INTO inventory_stock (item_id, location_id, quantity)
  VALUES (v_item_id, v_loc_id, 0)
  ON CONFLICT (item_id, location_id) DO NOTHING;

  SELECT quantity INTO v_stock_qty
  FROM inventory_stock
  WHERE item_id = v_item_id AND location_id = v_loc_id
  FOR UPDATE;

  IF v_stock_qty < p_qty THEN
    RAISE EXCEPTION 'Not enough inventory_stock for item_id=% at location_id=%. Stock=%, requested=%',
      v_item_id, v_loc_id, v_stock_qty, p_qty;
  END IF;

  -- Event log (GI)
  INSERT INTO movements (
    movement_type_id, item_id, quantity,
    from_location_id, to_location_id,
    reference_type, reference_id,
    user_id, notes
  )
  VALUES (
    v_mt_id, v_item_id, p_qty,
    v_loc_id, NULL,
    'container', v_container_id,
    p_user_id, p_notes
  )
  RETURNING id INTO v_movement_id;

  -- Update container state
  UPDATE stock_containers
  SET quantity = quantity - p_qty
  WHERE id = v_container_id;

  -- Update inventory_stock
  UPDATE inventory_stock
  SET quantity = quantity - p_qty, updated_at = now()
  WHERE item_id = v_item_id AND location_id = v_loc_id;

  -- OUTBOX
  PERFORM outbox_enqueue(
    'container',
    v_container_id,
    'container_consumed',
    jsonb_build_object(
      'container_code', p_container_code,
      'item_id', v_item_id,
      'location_id', v_loc_id,
      'qty', p_qty,
      'movement_id', v_movement_id,
      'notes', p_notes,
      'ts', now()
    )
  );

  RETURN v_movement_id;
END;
$$;


ALTER FUNCTION public.consume_from_container(p_container_code text, p_qty numeric, p_user_id bigint, p_notes text) OWNER TO postgres;

--
-- Name: issue_asset(text, bigint, text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.issue_asset(p_asset_code text, p_user_id bigint DEFAULT NULL::bigint, p_notes text DEFAULT NULL::text, p_new_status text DEFAULT 'inactive'::text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_asset_id BIGINT;
  v_item_id BIGINT;
  v_from_loc_id BIGINT;
  v_mt_id BIGINT;
  v_movement_id BIGINT;
BEGIN
  IF p_asset_code IS NULL OR length(trim(p_asset_code)) = 0 THEN
    RAISE EXCEPTION 'asset_code is required';
  END IF;

  -- Find asset and lock it
  SELECT id, item_id INTO v_asset_id, v_item_id
  FROM assets
  WHERE asset_code = p_asset_code
  FOR UPDATE;

  IF v_asset_id IS NULL THEN
    RAISE EXCEPTION 'Asset % not found', p_asset_code;
  END IF;

  -- Current location
  SELECT location_id INTO v_from_loc_id
  FROM asset_location
  WHERE asset_id = v_asset_id;

  -- GI movement type
  SELECT id INTO v_mt_id
  FROM movement_types
  WHERE code = 'GI';

  IF v_mt_id IS NULL THEN
    RAISE EXCEPTION 'movement_types code GI not found. Seed movement_types first.';
  END IF;

  -- Event log (GI)
  INSERT INTO movements (
    movement_type_id,
    item_id,
    quantity,
    from_location_id,
    to_location_id,
    reference_type,
    reference_id,
    user_id,
    notes
  )
  VALUES (
    v_mt_id,
    v_item_id,
    1,
    v_from_loc_id,
    NULL,
    'asset',
    v_asset_id,
    p_user_id,
    p_notes
  )
  RETURNING id INTO v_movement_id;

  -- Link movement <-> asset
  INSERT INTO movement_assets (movement_id, asset_id)
  VALUES (v_movement_id, v_asset_id);

  -- Remove current location (asset left the warehouse)
  DELETE FROM asset_location
  WHERE asset_id = v_asset_id;

  -- Update asset status
  UPDATE assets
  SET status = p_new_status
  WHERE id = v_asset_id;

  -- OUTBOX
  PERFORM outbox_enqueue(
    'asset',
    v_asset_id,
    'asset_issued',
    jsonb_build_object(
      'asset_code', p_asset_code,
      'item_id', v_item_id,
      'from_location_id', v_from_loc_id,
      'new_status', p_new_status,
      'movement_id', v_movement_id,
      'notes', p_notes,
      'ts', now()
    )
  );

  RETURN v_movement_id;
END;
$$;


ALTER FUNCTION public.issue_asset(p_asset_code text, p_user_id bigint, p_notes text, p_new_status text) OWNER TO postgres;

--
-- Name: move_asset_to_location(text, text, bigint, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.move_asset_to_location(p_asset_code text, p_to_location_code text, p_user_id bigint DEFAULT NULL::bigint, p_notes text DEFAULT NULL::text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_asset_id BIGINT;
  v_to_loc_id BIGINT;
  v_from_loc_id BIGINT;
  v_mt_id BIGINT;
  v_movement_id BIGINT;
BEGIN
  IF p_asset_code IS NULL OR length(trim(p_asset_code)) = 0 THEN
    RAISE EXCEPTION 'asset_code is required';
  END IF;

  -- Find asset
  SELECT id INTO v_asset_id
  FROM assets
  WHERE asset_code = p_asset_code;

  IF v_asset_id IS NULL THEN
    RAISE EXCEPTION 'Asset % not found', p_asset_code;
  END IF;

  -- Find destination location
  SELECT id INTO v_to_loc_id
  FROM locations
  WHERE code = p_to_location_code;

  IF v_to_loc_id IS NULL THEN
    RAISE EXCEPTION 'Location % not found', p_to_location_code;
  END IF;

  -- Current location (may not exist yet)
  SELECT location_id INTO v_from_loc_id
  FROM asset_location
  WHERE asset_id = v_asset_id;

  IF v_from_loc_id = v_to_loc_id THEN
    RAISE EXCEPTION 'Asset % is already at location %', p_asset_code, p_to_location_code;
  END IF;

  -- GT movement type
  SELECT id INTO v_mt_id
  FROM movement_types
  WHERE code = 'GT';

  IF v_mt_id IS NULL THEN
    RAISE EXCEPTION 'movement_types code GT not found. Seed movement_types first.';
  END IF;

  -- Event log
  INSERT INTO movements (
    movement_type_id,
    from_location_id, to_location_id,
    reference_type, reference_id,
    user_id, notes
  )
  VALUES (
    v_mt_id,
    v_from_loc_id, v_to_loc_id,
    'asset', v_asset_id,
    p_user_id, p_notes
  )
  RETURNING id INTO v_movement_id;

  -- Link movement <-> asset
  INSERT INTO movement_assets (movement_id, asset_id)
  VALUES (v_movement_id, v_asset_id);

  -- Update current state
  INSERT INTO asset_location (asset_id, location_id, since)
  VALUES (v_asset_id, v_to_loc_id, now())
  ON CONFLICT (asset_id)
  DO UPDATE SET location_id = EXCLUDED.location_id, since = EXCLUDED.since;

  -- OUTBOX
  PERFORM outbox_enqueue(
    'asset',
    v_asset_id,
    'asset_transferred',
    jsonb_build_object(
      'asset_code', p_asset_code,
      'from_location_id', v_from_loc_id,
      'to_location_code', p_to_location_code,
      'movement_id', v_movement_id,
      'notes', p_notes,
      'ts', now()
    )
  );

  RETURN v_movement_id;
END;
$$;


ALTER FUNCTION public.move_asset_to_location(p_asset_code text, p_to_location_code text, p_user_id bigint, p_notes text) OWNER TO postgres;

--
-- Name: outbox_enqueue(text, bigint, text, jsonb, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.outbox_enqueue(p_entity_type text, p_entity_id bigint, p_action text, p_payload jsonb, p_target_system text DEFAULT 'external_api'::text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_id BIGINT;
BEGIN
  INSERT INTO integration_outbox (
    direction, target_system, entity_type, entity_id, action,
    payload_json, status, retries, created_at
  )
  VALUES (
    'outbound',
    COALESCE(p_target_system, 'external_api'),
    p_entity_type,
    p_entity_id,
    p_action,
    COALESCE(p_payload, '{}'::jsonb),
    'pending',
    0,
    now()
  )
  RETURNING id INTO v_id;

  RETURN v_id;
END;
$$;


ALTER FUNCTION public.outbox_enqueue(p_entity_type text, p_entity_id bigint, p_action text, p_payload jsonb, p_target_system text) OWNER TO postgres;

--
-- Name: receive_asset(text, bigint, text, bigint, text, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.receive_asset(p_asset_code text, p_item_id bigint, p_to_location_code text, p_user_id bigint DEFAULT NULL::bigint, p_notes text DEFAULT NULL::text, p_create_enrichment boolean DEFAULT true) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_asset_id BIGINT;
  v_to_loc_id BIGINT;
  v_from_loc_id BIGINT;
  v_mt_id BIGINT;
  v_movement_id BIGINT;
  v_is_serialized BOOLEAN;
BEGIN
  IF p_asset_code IS NULL OR length(trim(p_asset_code)) = 0 THEN
    RAISE EXCEPTION 'asset_code is required';
  END IF;

  -- Validate item exists and is serialized
  SELECT is_serialized INTO v_is_serialized
  FROM items
  WHERE id = p_item_id;

  IF v_is_serialized IS NULL THEN
    RAISE EXCEPTION 'Item % not found', p_item_id;
  END IF;

  IF v_is_serialized = FALSE THEN
    RAISE EXCEPTION 'Cannot receive asset for non-serialized item_id=%', p_item_id
      USING ERRCODE = '23514';
  END IF;

  -- Destination location
  SELECT id INTO v_to_loc_id
  FROM locations
  WHERE code = p_to_location_code;

  IF v_to_loc_id IS NULL THEN
    RAISE EXCEPTION 'Location % not found', p_to_location_code;
  END IF;

  -- Ensure GR movement type exists
  SELECT id INTO v_mt_id
  FROM movement_types
  WHERE code = 'GR';

  IF v_mt_id IS NULL THEN
    RAISE EXCEPTION 'movement_types code GR not found. Seed movement_types first.';
  END IF;

  -- Ensure asset exists (lock if exists)
  SELECT id INTO v_asset_id
  FROM assets
  WHERE asset_code = p_asset_code
  FOR UPDATE;

  IF v_asset_id IS NULL THEN
    INSERT INTO assets (asset_code, item_id, status)
    VALUES (p_asset_code, p_item_id, 'active')
    RETURNING id INTO v_asset_id;
  ELSE
    -- Avoid changing product identity for same barcode/EPC
    IF EXISTS (
      SELECT 1 FROM assets
      WHERE id = v_asset_id
        AND item_id IS NOT NULL
        AND item_id <> p_item_id
    ) THEN
      RAISE EXCEPTION 'Asset % already exists with different item_id', p_asset_code
        USING ERRCODE = '23514';
    END IF;

    UPDATE assets
    SET item_id = COALESCE(item_id, p_item_id),
        status = 'active'
    WHERE id = v_asset_id;
  END IF;

  -- Current location (may be NULL)
  SELECT location_id INTO v_from_loc_id
  FROM asset_location
  WHERE asset_id = v_asset_id;

  -- Event log (GR)
  INSERT INTO movements (
    movement_type_id,
    item_id,
    quantity,
    from_location_id,
    to_location_id,
    reference_type,
    reference_id,
    user_id,
    notes
  )
  VALUES (
    v_mt_id,
    p_item_id,
    1,
    v_from_loc_id,
    v_to_loc_id,
    'asset',
    v_asset_id,
    p_user_id,
    p_notes
  )
  RETURNING id INTO v_movement_id;

  -- Link movement <-> asset
  INSERT INTO movement_assets (movement_id, asset_id)
  VALUES (v_movement_id, v_asset_id);

  -- Update current location
  INSERT INTO asset_location (asset_id, location_id, since)
  VALUES (v_asset_id, v_to_loc_id, now())
  ON CONFLICT (asset_id)
  DO UPDATE SET location_id = EXCLUDED.location_id, since = EXCLUDED.since;

  -- Optional enrichment
  IF p_create_enrichment THEN
    INSERT INTO asset_enrichment (asset_id, sync_status, retries)
    VALUES (v_asset_id, 'pending', 0)
    ON CONFLICT (asset_id) DO NOTHING;
  END IF;

  -- OUTBOX
  PERFORM outbox_enqueue(
    'asset',
    v_asset_id,
    'asset_received',
    jsonb_build_object(
      'asset_code', p_asset_code,
      'item_id', p_item_id,
      'to_location_code', p_to_location_code,
      'movement_id', v_movement_id,
      'notes', p_notes,
      'ts', now()
    )
  );

  RETURN v_movement_id;
END;
$$;


ALTER FUNCTION public.receive_asset(p_asset_code text, p_item_id bigint, p_to_location_code text, p_user_id bigint, p_notes text, p_create_enrichment boolean) OWNER TO postgres;

--
-- Name: receive_container(text, bigint, text, numeric, bigint, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.receive_container(p_container_code text, p_item_id bigint, p_location_code text, p_qty numeric, p_user_id bigint DEFAULT NULL::bigint, p_notes text DEFAULT NULL::text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_loc_id BIGINT;
  v_container_id BIGINT;
  v_mt_id BIGINT;
  v_movement_id BIGINT;
BEGIN
  IF p_container_code IS NULL OR length(trim(p_container_code)) = 0 THEN
    RAISE EXCEPTION 'container_code is required';
  END IF;

  IF p_qty IS NULL OR p_qty <= 0 THEN
    RAISE EXCEPTION 'Quantity must be > 0';
  END IF;

  -- Find location
  SELECT id INTO v_loc_id
  FROM locations
  WHERE code = p_location_code;

  IF v_loc_id IS NULL THEN
    RAISE EXCEPTION 'Location % not found', p_location_code;
  END IF;

  -- Ensure GR movement type exists
  SELECT id INTO v_mt_id
  FROM movement_types
  WHERE code = 'GR';

  IF v_mt_id IS NULL THEN
    RAISE EXCEPTION 'movement_types code GR not found. Seed movement_types first.';
  END IF;

  -- Create container if needed, else add quantity (lock row to avoid race)
  SELECT id INTO v_container_id
  FROM stock_containers
  WHERE container_code = p_container_code
  FOR UPDATE;

  IF v_container_id IS NULL THEN
    INSERT INTO stock_containers (container_code, item_id, location_id, quantity, status)
    VALUES (p_container_code, p_item_id, v_loc_id, p_qty, 'open')
    RETURNING id INTO v_container_id;
  ELSE
    UPDATE stock_containers
    SET quantity = quantity + p_qty,
        location_id = v_loc_id
    WHERE id = v_container_id;
  END IF;

  -- Event log (GR)
  INSERT INTO movements (
    movement_type_id, item_id, quantity,
    from_location_id, to_location_id,
    reference_type, reference_id,
    user_id, notes
  )
  VALUES (
    v_mt_id, p_item_id, p_qty,
    NULL, v_loc_id,
    'container', v_container_id,
    p_user_id, p_notes
  )
  RETURNING id INTO v_movement_id;

  -- Update inventory_stock (increase)
  INSERT INTO inventory_stock (item_id, location_id, quantity)
  VALUES (p_item_id, v_loc_id, p_qty)
  ON CONFLICT (item_id, location_id)
  DO UPDATE SET quantity = inventory_stock.quantity + EXCLUDED.quantity,
               updated_at = now();

  -- OUTBOX
  PERFORM outbox_enqueue(
    'container',
    v_container_id,
    'container_received',
    jsonb_build_object(
      'container_code', p_container_code,
      'item_id', p_item_id,
      'location_code', p_location_code,
      'qty', p_qty,
      'movement_id', v_movement_id,
      'notes', p_notes,
      'ts', now()
    )
  );

  RETURN v_movement_id;
END;
$$;


ALTER FUNCTION public.receive_container(p_container_code text, p_item_id bigint, p_location_code text, p_qty numeric, p_user_id bigint, p_notes text) OWNER TO postgres;

--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_updated_at() OWNER TO postgres;

--
-- Name: transfer_container(text, text, bigint, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.transfer_container(p_container_code text, p_to_location_code text, p_user_id bigint DEFAULT NULL::bigint, p_notes text DEFAULT NULL::text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_container_id BIGINT;
  v_item_id BIGINT;
  v_from_loc_id BIGINT;
  v_to_loc_id BIGINT;
  v_qty NUMERIC;
  v_mt_id BIGINT;
  v_movement_id BIGINT;
  v_from_stock NUMERIC;
BEGIN
  IF p_container_code IS NULL OR length(trim(p_container_code)) = 0 THEN
    RAISE EXCEPTION 'container_code is required';
  END IF;

  -- Lock container row
  SELECT id, item_id, location_id, quantity
  INTO v_container_id, v_item_id, v_from_loc_id, v_qty
  FROM stock_containers
  WHERE container_code = p_container_code
  FOR UPDATE;

  IF v_container_id IS NULL THEN
    RAISE EXCEPTION 'Container % not found', p_container_code;
  END IF;

  -- Destination location
  SELECT id INTO v_to_loc_id
  FROM locations
  WHERE code = p_to_location_code;

  IF v_to_loc_id IS NULL THEN
    RAISE EXCEPTION 'Location % not found', p_to_location_code;
  END IF;

  IF v_from_loc_id = v_to_loc_id THEN
    RAISE EXCEPTION 'Container % is already at location %', p_container_code, p_to_location_code;
  END IF;

  -- Ensure GT movement type exists
  SELECT id INTO v_mt_id
  FROM movement_types
  WHERE code = 'GT';

  IF v_mt_id IS NULL THEN
    RAISE EXCEPTION 'movement_types code GT not found. Seed movement_types first.';
  END IF;

  -- Ensure stock rows exist and lock origin row
  INSERT INTO inventory_stock (item_id, location_id, quantity)
  VALUES (v_item_id, v_from_loc_id, 0)
  ON CONFLICT (item_id, location_id) DO NOTHING;

  INSERT INTO inventory_stock (item_id, location_id, quantity)
  VALUES (v_item_id, v_to_loc_id, 0)
  ON CONFLICT (item_id, location_id) DO NOTHING;

  SELECT quantity INTO v_from_stock
  FROM inventory_stock
  WHERE item_id = v_item_id AND location_id = v_from_loc_id
  FOR UPDATE;

  IF v_from_stock < v_qty THEN
    RAISE EXCEPTION 'inventory_stock at origin is inconsistent. item_id=% loc_id=% stock=% container_qty=%',
      v_item_id, v_from_loc_id, v_from_stock, v_qty;
  END IF;

  -- Event log (GT)
  INSERT INTO movements (
    movement_type_id, item_id, quantity,
    from_location_id, to_location_id,
    reference_type, reference_id,
    user_id, notes
  )
  VALUES (
    v_mt_id, v_item_id, v_qty,
    v_from_loc_id, v_to_loc_id,
    'container', v_container_id,
    p_user_id, p_notes
  )
  RETURNING id INTO v_movement_id;

  -- Move container location
  UPDATE stock_containers
  SET location_id = v_to_loc_id
  WHERE id = v_container_id;

  -- Move stock between locations (total unchanged)
  UPDATE inventory_stock
  SET quantity = quantity - v_qty, updated_at = now()
  WHERE item_id = v_item_id AND location_id = v_from_loc_id;

  UPDATE inventory_stock
  SET quantity = quantity + v_qty, updated_at = now()
  WHERE item_id = v_item_id AND location_id = v_to_loc_id;

  -- OUTBOX
  PERFORM outbox_enqueue(
    'container',
    v_container_id,
    'container_transferred',
    jsonb_build_object(
      'container_code', p_container_code,
      'item_id', v_item_id,
      'from_location_id', v_from_loc_id,
      'to_location_id', v_to_loc_id,
      'qty', v_qty,
      'movement_id', v_movement_id,
      'notes', p_notes,
      'ts', now()
    )
  );

  RETURN v_movement_id;
END;
$$;


ALTER FUNCTION public.transfer_container(p_container_code text, p_to_location_code text, p_user_id bigint, p_notes text) OWNER TO postgres;

--
-- Name: trg_assets_item_must_be_serialized(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trg_assets_item_must_be_serialized() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_is_serialized boolean;
BEGIN
  IF NEW.item_id IS NULL THEN
    RETURN NEW;
  END IF;

  SELECT is_serialized INTO v_is_serialized
  FROM items
  WHERE id = NEW.item_id;

  IF v_is_serialized IS NULL THEN
    RAISE EXCEPTION 'Item % does not exist', NEW.item_id;
  END IF;

  IF v_is_serialized = FALSE THEN
    RAISE EXCEPTION 'Cannot create asset for non-serialized item_id=%', NEW.item_id
      USING ERRCODE = '23514';
  END IF;

  RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_assets_item_must_be_serialized() OWNER TO postgres;

--
-- Name: trg_movement_assets_single_item(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trg_movement_assets_single_item() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_movement_id bigint;
  v_item_count int;
BEGIN
  v_movement_id := COALESCE(NEW.movement_id, OLD.movement_id);

  SELECT COUNT(DISTINCT a.item_id)
    INTO v_item_count
  FROM movement_assets ma
  JOIN assets a ON a.id = ma.asset_id
  WHERE ma.movement_id = v_movement_id;

  IF v_item_count > 1 THEN
    RAISE EXCEPTION 'movement_id % contains assets from different items', v_movement_id
      USING ERRCODE = '23514';
  END IF;

  RETURN NULL;
END;
$$;


ALTER FUNCTION public.trg_movement_assets_single_item() OWNER TO postgres;

--
-- Name: trg_movements_validate_reference(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trg_movements_validate_reference() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_exists boolean;
BEGIN
  IF NEW.reference_type IS NULL AND NEW.reference_id IS NULL THEN
    RETURN NEW;
  END IF;

  IF NEW.reference_type IS NULL OR NEW.reference_id IS NULL THEN
    RAISE EXCEPTION 'reference_type and reference_id must be both NULL or both NOT NULL'
      USING ERRCODE = '23514';
  END IF;

  IF NEW.reference_type = 'asset' THEN
    SELECT EXISTS (SELECT 1 FROM assets WHERE id = NEW.reference_id) INTO v_exists;
  ELSIF NEW.reference_type = 'container' THEN
    SELECT EXISTS (SELECT 1 FROM stock_containers WHERE id = NEW.reference_id) INTO v_exists;
  ELSE
    RAISE EXCEPTION 'Invalid reference_type %', NEW.reference_type USING ERRCODE = '23514';
  END IF;

  IF NOT v_exists THEN
    RAISE EXCEPTION 'Reference %/% does not exist', NEW.reference_type, NEW.reference_id
      USING ERRCODE = '23503';
  END IF;

  RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_movements_validate_reference() OWNER TO postgres;

--
-- Name: trg_stock_containers_item_must_be_non_serialized(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trg_stock_containers_item_must_be_non_serialized() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_is_serialized boolean;
BEGIN
  SELECT is_serialized INTO v_is_serialized
  FROM items
  WHERE id = NEW.item_id;

  IF v_is_serialized IS NULL THEN
    RAISE EXCEPTION 'Item % does not exist', NEW.item_id;
  END IF;

  IF v_is_serialized = TRUE THEN
    RAISE EXCEPTION 'Cannot create stock_container for serialized item_id=%', NEW.item_id
      USING ERRCODE = '23514';
  END IF;

  RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_stock_containers_item_must_be_non_serialized() OWNER TO postgres;

--
-- Name: trg_stock_containers_status_by_qty(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trg_stock_containers_status_by_qty() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW.quantity <= 0 THEN
    NEW.status := 'empty';
  ELSIF NEW.status = 'empty' THEN
    NEW.status := 'open';
  END IF;
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_stock_containers_status_by_qty() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: asset_enrichment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.asset_enrichment (
    asset_id bigint NOT NULL,
    serial_number text,
    sync_status text DEFAULT 'pending'::text NOT NULL,
    last_sync_at timestamp with time zone,
    last_error text,
    retries integer DEFAULT 0 NOT NULL,
    CONSTRAINT asset_enrichment_retries_ck CHECK ((retries >= 0)),
    CONSTRAINT asset_enrichment_status_ck CHECK ((sync_status = ANY (ARRAY['pending'::text, 'ok'::text, 'not_found'::text, 'error'::text])))
);


ALTER TABLE public.asset_enrichment OWNER TO postgres;

--
-- Name: asset_location; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.asset_location (
    asset_id bigint NOT NULL,
    location_id bigint NOT NULL,
    since timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.asset_location OWNER TO postgres;

--
-- Name: assets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.assets (
    id bigint NOT NULL,
    asset_code text NOT NULL,
    item_id bigint,
    status text DEFAULT 'active'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT assets_status_ck CHECK ((status = ANY (ARRAY['active'::text, 'repair'::text, 'scrapped'::text, 'lost'::text, 'inactive'::text])))
);


ALTER TABLE public.assets OWNER TO postgres;

--
-- Name: assets_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.assets_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.assets_id_seq OWNER TO postgres;

--
-- Name: assets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.assets_id_seq OWNED BY public.assets.id;


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_log (
    id bigint NOT NULL,
    at timestamp with time zone DEFAULT now() NOT NULL,
    user_id bigint,
    action text NOT NULL,
    entity_type text NOT NULL,
    entity_id bigint NOT NULL,
    before_json jsonb,
    after_json jsonb,
    request_id text
);


ALTER TABLE public.audit_log OWNER TO postgres;

--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_log_id_seq OWNER TO postgres;

--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_log_id_seq OWNED BY public.audit_log.id;


--
-- Name: error_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.error_log (
    id bigint NOT NULL,
    happened_at timestamp with time zone DEFAULT now() NOT NULL,
    severity text NOT NULL,
    source text NOT NULL,
    operation text,
    entity_type text,
    entity_id bigint,
    user_id bigint,
    request_id text,
    message text NOT NULL,
    exception_type text,
    stacktrace text,
    metadata_json jsonb,
    resolved_at timestamp with time zone,
    resolved_by bigint,
    resolution_notes text,
    CONSTRAINT error_log_severity_ck CHECK ((severity = ANY (ARRAY['info'::text, 'warning'::text, 'error'::text, 'critical'::text])))
);


ALTER TABLE public.error_log OWNER TO postgres;

--
-- Name: error_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.error_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.error_log_id_seq OWNER TO postgres;

--
-- Name: error_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.error_log_id_seq OWNED BY public.error_log.id;


--
-- Name: integration_outbox; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.integration_outbox (
    id bigint NOT NULL,
    direction text DEFAULT 'outbound'::text NOT NULL,
    target_system text DEFAULT 'external_api'::text NOT NULL,
    entity_type text NOT NULL,
    entity_id bigint NOT NULL,
    action text NOT NULL,
    payload_json jsonb NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    retries integer DEFAULT 0 NOT NULL,
    last_attempt_at timestamp with time zone,
    next_retry_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT outbox_direction_ck CHECK ((direction = ANY (ARRAY['outbound'::text, 'inbound'::text]))),
    CONSTRAINT outbox_retries_ck CHECK ((retries >= 0)),
    CONSTRAINT outbox_status_ck CHECK ((status = ANY (ARRAY['pending'::text, 'sent'::text, 'error'::text])))
);


ALTER TABLE public.integration_outbox OWNER TO postgres;

--
-- Name: integration_outbox_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.integration_outbox_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.integration_outbox_id_seq OWNER TO postgres;

--
-- Name: integration_outbox_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.integration_outbox_id_seq OWNED BY public.integration_outbox.id;


--
-- Name: inventory_stock; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inventory_stock (
    id bigint NOT NULL,
    item_id bigint NOT NULL,
    location_id bigint NOT NULL,
    quantity numeric(18,6) DEFAULT 0 NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT inventory_stock_qty_ck CHECK ((quantity >= (0)::numeric))
);


ALTER TABLE public.inventory_stock OWNER TO postgres;

--
-- Name: inventory_stock_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.inventory_stock_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inventory_stock_id_seq OWNER TO postgres;

--
-- Name: inventory_stock_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.inventory_stock_id_seq OWNED BY public.inventory_stock.id;


--
-- Name: items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.items (
    id bigint NOT NULL,
    name text NOT NULL,
    description text,
    category text,
    uom text NOT NULL,
    is_serialized boolean DEFAULT false NOT NULL,
    min_stock numeric(18,6),
    reorder_point numeric(18,6),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    item_code text,
    CONSTRAINT items_stock_levels_ck CHECK ((((min_stock IS NULL) OR (min_stock >= (0)::numeric)) AND ((reorder_point IS NULL) OR (reorder_point >= (0)::numeric)) AND ((min_stock IS NULL) OR (reorder_point IS NULL) OR (reorder_point >= min_stock))))
);


ALTER TABLE public.items OWNER TO postgres;

--
-- Name: items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.items_id_seq OWNER TO postgres;

--
-- Name: items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.items_id_seq OWNED BY public.items.id;


--
-- Name: locations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.locations (
    id bigint NOT NULL,
    code text NOT NULL,
    name text NOT NULL,
    type text NOT NULL,
    parent_id bigint,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE public.locations OWNER TO postgres;

--
-- Name: locations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.locations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.locations_id_seq OWNER TO postgres;

--
-- Name: locations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.locations_id_seq OWNED BY public.locations.id;


--
-- Name: movement_assets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movement_assets (
    movement_id bigint NOT NULL,
    asset_id bigint NOT NULL
);


ALTER TABLE public.movement_assets OWNER TO postgres;

--
-- Name: movement_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movement_types (
    id bigint NOT NULL,
    code text NOT NULL,
    name text NOT NULL,
    affects_stock boolean NOT NULL,
    affects_location boolean NOT NULL,
    stock_sign smallint NOT NULL,
    CONSTRAINT movement_types_sign_logic_ck CHECK ((((affects_stock = false) AND (stock_sign = 0)) OR ((affects_stock = true) AND (stock_sign = ANY (ARRAY['-1'::integer, 1]))))),
    CONSTRAINT movement_types_stock_sign_ck CHECK ((stock_sign = ANY (ARRAY['-1'::integer, 0, 1])))
);


ALTER TABLE public.movement_types OWNER TO postgres;

--
-- Name: movement_types_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.movement_types_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movement_types_id_seq OWNER TO postgres;

--
-- Name: movement_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.movement_types_id_seq OWNED BY public.movement_types.id;


--
-- Name: movements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movements (
    id bigint NOT NULL,
    movement_type_id bigint NOT NULL,
    item_id bigint,
    quantity numeric(18,6),
    from_location_id bigint,
    to_location_id bigint,
    reference_type text,
    reference_id bigint,
    user_id bigint,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    notes text,
    CONSTRAINT movements_qty_ck CHECK (((quantity IS NULL) OR (quantity >= (0)::numeric))),
    CONSTRAINT movements_ref_pair_ck CHECK ((((reference_type IS NULL) AND (reference_id IS NULL)) OR ((reference_type IS NOT NULL) AND (reference_id IS NOT NULL)))),
    CONSTRAINT movements_ref_type_ck CHECK (((reference_type IS NULL) OR (reference_type = ANY (ARRAY['asset'::text, 'container'::text]))))
);


ALTER TABLE public.movements OWNER TO postgres;

--
-- Name: movements_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.movements_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movements_id_seq OWNER TO postgres;

--
-- Name: movements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.movements_id_seq OWNED BY public.movements.id;


--
-- Name: stock_containers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.stock_containers (
    id bigint NOT NULL,
    container_code text NOT NULL,
    item_id bigint NOT NULL,
    location_id bigint NOT NULL,
    quantity numeric(18,6) DEFAULT 0 NOT NULL,
    status text DEFAULT 'open'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    CONSTRAINT stock_containers_qty_ck CHECK ((quantity >= (0)::numeric)),
    CONSTRAINT stock_containers_status_ck CHECK ((status = ANY (ARRAY['open'::text, 'empty'::text, 'discarded'::text])))
);


ALTER TABLE public.stock_containers OWNER TO postgres;

--
-- Name: stock_containers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.stock_containers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.stock_containers_id_seq OWNER TO postgres;

--
-- Name: stock_containers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.stock_containers_id_seq OWNED BY public.stock_containers.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    username text NOT NULL,
    full_name text NOT NULL,
    email text,
    role text NOT NULL,
    department text,
    is_active boolean DEFAULT true NOT NULL,
    password_hash text,
    auth_provider text DEFAULT 'local'::text NOT NULL,
    last_login_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT users_auth_provider_ck CHECK ((auth_provider = ANY (ARRAY['local'::text, 'ldap'::text, 'sso'::text, 'rfid'::text])))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: assets id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assets ALTER COLUMN id SET DEFAULT nextval('public.assets_id_seq'::regclass);


--
-- Name: audit_log id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN id SET DEFAULT nextval('public.audit_log_id_seq'::regclass);


--
-- Name: error_log id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.error_log ALTER COLUMN id SET DEFAULT nextval('public.error_log_id_seq'::regclass);


--
-- Name: integration_outbox id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.integration_outbox ALTER COLUMN id SET DEFAULT nextval('public.integration_outbox_id_seq'::regclass);


--
-- Name: inventory_stock id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_stock ALTER COLUMN id SET DEFAULT nextval('public.inventory_stock_id_seq'::regclass);


--
-- Name: items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items ALTER COLUMN id SET DEFAULT nextval('public.items_id_seq'::regclass);


--
-- Name: locations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locations ALTER COLUMN id SET DEFAULT nextval('public.locations_id_seq'::regclass);


--
-- Name: movement_types id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movement_types ALTER COLUMN id SET DEFAULT nextval('public.movement_types_id_seq'::regclass);


--
-- Name: movements id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movements ALTER COLUMN id SET DEFAULT nextval('public.movements_id_seq'::regclass);


--
-- Name: stock_containers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stock_containers ALTER COLUMN id SET DEFAULT nextval('public.stock_containers_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: asset_enrichment; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.asset_enrichment (asset_id, serial_number, sync_status, last_sync_at, last_error, retries) FROM stdin;
1	\N	pending	\N	\N	0
\.


--
-- Data for Name: asset_location; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.asset_location (asset_id, location_id, since) FROM stdin;
6	2	2026-02-09 13:07:45.319201+01
\.


--
-- Data for Name: assets; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.assets (id, asset_code, item_id, status, created_at, updated_at) FROM stdin;
1	ITC-015647	4	inactive	2026-02-05 11:41:41.747964+01	2026-02-05 12:11:39.668012+01
6	EPC123	5	active	2026-02-09 13:07:45.319201+01	2026-02-09 13:07:45.319201+01
\.


--
-- Data for Name: audit_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_log (id, at, user_id, action, entity_type, entity_id, before_json, after_json, request_id) FROM stdin;
\.


--
-- Data for Name: error_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.error_log (id, happened_at, severity, source, operation, entity_type, entity_id, user_id, request_id, message, exception_type, stacktrace, metadata_json, resolved_at, resolved_by, resolution_notes) FROM stdin;
\.


--
-- Data for Name: integration_outbox; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.integration_outbox (id, direction, target_system, entity_type, entity_id, action, payload_json, status, retries, last_attempt_at, next_retry_at, created_at) FROM stdin;
1	outbound	external_api	test	1	ping	{}	sent	0	2026-02-05 14:09:12.378714+01	\N	2026-02-05 13:59:35.567183+01
\.


--
-- Data for Name: inventory_stock; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inventory_stock (id, item_id, location_id, quantity, updated_at) FROM stdin;
1	1	5	0.000000	2026-02-05 11:33:16.993811+01
4	1	6	90.000000	2026-02-05 11:33:16.993811+01
\.


--
-- Data for Name: items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.items (id, name, description, category, uom, is_serialized, min_stock, reorder_point, is_active, created_at, updated_at, item_code) FROM stdin;
4	Tablet	\N	\N	pcs	t	2.000000	4.000000	t	2026-02-05 10:29:59.591826+01	2026-02-05 12:01:27.65446+01	TAB-STD
1	Tornillos M4	\N	\N	pcs	f	\N	\N	t	2026-02-05 09:50:03.902468+01	2026-02-05 12:01:27.664481+01	TOR-M4
5	RFID Card Instructor	Temporary instructor card	CARD	EA	t	0.000000	10.000000	t	2026-02-09 12:41:06.337915+01	2026-02-09 12:41:06.337915+01	CARD-INSTR
\.


--
-- Data for Name: locations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.locations (id, code, name, type, parent_id, is_active) FROM stdin;
1	ALM-01	Almac‚n central	warehouse	\N	t
2	ALM	Warehouse	warehouse	\N	t
5	ALM-A	Zone A	zone	2	t
6	ALM-B	Zone B	zone	2	t
\.


--
-- Data for Name: movement_assets; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.movement_assets (movement_id, asset_id) FROM stdin;
4	1
5	1
6	1
7	1
8	1
9	1
10	1
\.


--
-- Data for Name: movement_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.movement_types (id, code, name, affects_stock, affects_location, stock_sign) FROM stdin;
1	GR	Goods Receipt	t	t	1
2	GI	Goods Issue	t	t	-1
3	GT	Goods Transfer	f	t	0
4	ADJ+	Adjustment +	t	t	1
5	ADJ-	Adjustment -	t	t	-1
6	INFO	Info	f	f	0
\.


--
-- Data for Name: movements; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.movements (id, movement_type_id, item_id, quantity, from_location_id, to_location_id, reference_type, reference_id, user_id, created_at, notes) FROM stdin;
1	1	1	100.000000	\N	5	container	1	\N	2026-02-05 11:33:07.130738+01	GR 100 pcs
2	2	1	10.000000	5	\N	container	1	\N	2026-02-05 11:33:12.882983+01	GI 10 pcs
3	3	1	90.000000	5	6	container	1	\N	2026-02-05 11:33:16.993811+01	GT pack to ALM-B
4	1	4	1.000000	\N	5	asset	1	\N	2026-02-05 11:41:41.747964+01	GR asset
5	1	4	1.000000	5	5	asset	1	\N	2026-02-05 11:41:51.221927+01	GR asset
6	1	4	1.000000	5	5	asset	1	\N	2026-02-05 11:59:46.523565+01	GR asset
7	1	4	1.000000	5	5	asset	1	\N	2026-02-05 12:00:06.428118+01	GR asset
8	1	4	1.000000	5	5	asset	1	\N	2026-02-05 12:01:38.856052+01	GR asset
9	3	\N	\N	5	6	asset	1	\N	2026-02-05 12:11:27.163759+01	GT asset to ALM-B
10	2	4	1.000000	6	\N	asset	1	\N	2026-02-05 12:11:39.668012+01	GI issued to simulator
11	1	4	5.000000	\N	2	\N	\N	1	2026-02-09 14:18:22.369514+01	Initial stock
12	1	4	5.000000	\N	2	\N	\N	1	2026-02-09 14:18:25.483612+01	Initial stock
\.


--
-- Data for Name: stock_containers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.stock_containers (id, container_code, item_id, location_id, quantity, status, created_at, updated_at, is_active) FROM stdin;
1	GEN-18606	1	6	90.000000	open	2026-02-05 11:33:07.130738+01	2026-02-05 11:33:16.993811+01	t
2	1234	1	5	100.000000	open	2026-02-09 14:01:20.874533+01	2026-02-09 14:01:20.874533+01	t
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, full_name, email, role, department, is_active, password_hash, auth_provider, last_login_at, created_at, updated_at) FROM stdin;
1	acardona	Adrian Cardona Ruiz	\N	Admin	string	t	string	local	\N	2026-02-09 10:53:36.702602+01	2026-02-09 11:14:53.176195+01
\.


--
-- Name: assets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.assets_id_seq', 6, true);


--
-- Name: audit_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_log_id_seq', 1, false);


--
-- Name: error_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.error_log_id_seq', 1, false);


--
-- Name: integration_outbox_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.integration_outbox_id_seq', 1, true);


--
-- Name: inventory_stock_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inventory_stock_id_seq', 4, true);


--
-- Name: items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.items_id_seq', 5, true);


--
-- Name: locations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.locations_id_seq', 7, true);


--
-- Name: movement_types_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.movement_types_id_seq', 6, true);


--
-- Name: movements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.movements_id_seq', 12, true);


--
-- Name: stock_containers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.stock_containers_id_seq', 2, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: asset_enrichment asset_enrichment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asset_enrichment
    ADD CONSTRAINT asset_enrichment_pkey PRIMARY KEY (asset_id);


--
-- Name: asset_location asset_location_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asset_location
    ADD CONSTRAINT asset_location_pkey PRIMARY KEY (asset_id);


--
-- Name: assets assets_asset_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_asset_code_key UNIQUE (asset_code);


--
-- Name: assets assets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_pkey PRIMARY KEY (id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: error_log error_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.error_log
    ADD CONSTRAINT error_log_pkey PRIMARY KEY (id);


--
-- Name: integration_outbox integration_outbox_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.integration_outbox
    ADD CONSTRAINT integration_outbox_pkey PRIMARY KEY (id);


--
-- Name: inventory_stock inventory_stock_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_stock
    ADD CONSTRAINT inventory_stock_pkey PRIMARY KEY (id);


--
-- Name: items items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_pkey PRIMARY KEY (id);


--
-- Name: locations locations_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locations
    ADD CONSTRAINT locations_code_key UNIQUE (code);


--
-- Name: locations locations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locations
    ADD CONSTRAINT locations_pkey PRIMARY KEY (id);


--
-- Name: movement_assets movement_assets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movement_assets
    ADD CONSTRAINT movement_assets_pkey PRIMARY KEY (movement_id, asset_id);


--
-- Name: movement_types movement_types_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movement_types
    ADD CONSTRAINT movement_types_code_key UNIQUE (code);


--
-- Name: movement_types movement_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movement_types
    ADD CONSTRAINT movement_types_pkey PRIMARY KEY (id);


--
-- Name: movements movements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movements
    ADD CONSTRAINT movements_pkey PRIMARY KEY (id);


--
-- Name: stock_containers stock_containers_container_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stock_containers
    ADD CONSTRAINT stock_containers_container_code_key UNIQUE (container_code);


--
-- Name: stock_containers stock_containers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stock_containers
    ADD CONSTRAINT stock_containers_pkey PRIMARY KEY (id);


--
-- Name: inventory_stock uq_inventory_stock_item_loc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_stock
    ADD CONSTRAINT uq_inventory_stock_item_loc UNIQUE (item_id, location_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_asset_enrichment_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_asset_enrichment_status ON public.asset_enrichment USING btree (sync_status);


--
-- Name: idx_asset_location_loc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_asset_location_loc ON public.asset_location USING btree (location_id);


--
-- Name: idx_assets_item; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_assets_item ON public.assets USING btree (item_id);


--
-- Name: idx_audit_log_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_log_at ON public.audit_log USING btree (at);


--
-- Name: idx_audit_log_entity; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_log_entity ON public.audit_log USING btree (entity_type, entity_id);


--
-- Name: idx_audit_log_request; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_log_request ON public.audit_log USING btree (request_id);


--
-- Name: idx_audit_log_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_log_user ON public.audit_log USING btree (user_id);


--
-- Name: idx_error_log_request; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_log_request ON public.error_log USING btree (request_id);


--
-- Name: idx_error_log_sev_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_log_sev_time ON public.error_log USING btree (severity, happened_at);


--
-- Name: idx_error_log_source; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_log_source ON public.error_log USING btree (source, happened_at);


--
-- Name: idx_error_log_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_log_time ON public.error_log USING btree (happened_at);


--
-- Name: idx_error_log_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_log_user ON public.error_log USING btree (user_id, happened_at);


--
-- Name: idx_inventory_stock_item; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_inventory_stock_item ON public.inventory_stock USING btree (item_id);


--
-- Name: idx_inventory_stock_loc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_inventory_stock_loc ON public.inventory_stock USING btree (location_id);


--
-- Name: idx_items_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_items_category ON public.items USING btree (category);


--
-- Name: idx_locations_parent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_locations_parent ON public.locations USING btree (parent_id);


--
-- Name: idx_movement_assets_asset; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movement_assets_asset ON public.movement_assets USING btree (asset_id);


--
-- Name: idx_movements_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movements_created_at ON public.movements USING btree (created_at);


--
-- Name: idx_movements_from_loc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movements_from_loc ON public.movements USING btree (from_location_id);


--
-- Name: idx_movements_item; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movements_item ON public.movements USING btree (item_id);


--
-- Name: idx_movements_to_loc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movements_to_loc ON public.movements USING btree (to_location_id);


--
-- Name: idx_movements_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movements_type ON public.movements USING btree (movement_type_id);


--
-- Name: idx_movements_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movements_user ON public.movements USING btree (user_id);


--
-- Name: idx_outbox_entity; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_outbox_entity ON public.integration_outbox USING btree (entity_type, entity_id);


--
-- Name: idx_outbox_pick; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_outbox_pick ON public.integration_outbox USING btree (status, next_retry_at NULLS FIRST, created_at);


--
-- Name: idx_stock_containers_item; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_stock_containers_item ON public.stock_containers USING btree (item_id);


--
-- Name: idx_stock_containers_loc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_stock_containers_loc ON public.stock_containers USING btree (location_id);


--
-- Name: uq_items_item_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_items_item_code ON public.items USING btree (item_code) WHERE (item_code IS NOT NULL);


--
-- Name: movement_assets ct_movement_assets_single_item; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE CONSTRAINT TRIGGER ct_movement_assets_single_item AFTER INSERT OR DELETE OR UPDATE ON public.movement_assets DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.trg_movement_assets_single_item();


--
-- Name: assets t_assets_serialized_only; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER t_assets_serialized_only BEFORE INSERT OR UPDATE OF item_id ON public.assets FOR EACH ROW EXECUTE FUNCTION public.trg_assets_item_must_be_serialized();


--
-- Name: movements t_movements_validate_reference; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER t_movements_validate_reference BEFORE INSERT OR UPDATE OF reference_type, reference_id ON public.movements FOR EACH ROW EXECUTE FUNCTION public.trg_movements_validate_reference();


--
-- Name: stock_containers t_stock_containers_non_serialized; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER t_stock_containers_non_serialized BEFORE INSERT OR UPDATE OF item_id ON public.stock_containers FOR EACH ROW EXECUTE FUNCTION public.trg_stock_containers_item_must_be_non_serialized();


--
-- Name: stock_containers t_stock_containers_status_qty; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER t_stock_containers_status_qty BEFORE INSERT OR UPDATE OF quantity, status ON public.stock_containers FOR EACH ROW EXECUTE FUNCTION public.trg_stock_containers_status_by_qty();


--
-- Name: assets trg_assets_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_assets_updated_at BEFORE UPDATE ON public.assets FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: items trg_items_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_items_updated_at BEFORE UPDATE ON public.items FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: stock_containers trg_stock_containers_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_stock_containers_updated_at BEFORE UPDATE ON public.stock_containers FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: users trg_users_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: asset_enrichment asset_enrichment_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asset_enrichment
    ADD CONSTRAINT asset_enrichment_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Name: asset_location asset_location_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asset_location
    ADD CONSTRAINT asset_location_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Name: asset_location asset_location_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asset_location
    ADD CONSTRAINT asset_location_location_id_fkey FOREIGN KEY (location_id) REFERENCES public.locations(id) ON DELETE RESTRICT;


--
-- Name: assets assets_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id) ON DELETE SET NULL;


--
-- Name: audit_log audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: error_log error_log_resolved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.error_log
    ADD CONSTRAINT error_log_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: error_log error_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.error_log
    ADD CONSTRAINT error_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: inventory_stock inventory_stock_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_stock
    ADD CONSTRAINT inventory_stock_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id) ON DELETE CASCADE;


--
-- Name: inventory_stock inventory_stock_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_stock
    ADD CONSTRAINT inventory_stock_location_id_fkey FOREIGN KEY (location_id) REFERENCES public.locations(id) ON DELETE CASCADE;


--
-- Name: locations locations_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locations
    ADD CONSTRAINT locations_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.locations(id) ON DELETE SET NULL;


--
-- Name: movement_assets movement_assets_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movement_assets
    ADD CONSTRAINT movement_assets_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE RESTRICT;


--
-- Name: movement_assets movement_assets_movement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movement_assets
    ADD CONSTRAINT movement_assets_movement_id_fkey FOREIGN KEY (movement_id) REFERENCES public.movements(id) ON DELETE CASCADE;


--
-- Name: movements movements_from_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movements
    ADD CONSTRAINT movements_from_location_id_fkey FOREIGN KEY (from_location_id) REFERENCES public.locations(id) ON DELETE SET NULL;


--
-- Name: movements movements_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movements
    ADD CONSTRAINT movements_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id) ON DELETE SET NULL;


--
-- Name: movements movements_movement_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movements
    ADD CONSTRAINT movements_movement_type_id_fkey FOREIGN KEY (movement_type_id) REFERENCES public.movement_types(id) ON DELETE RESTRICT;


--
-- Name: movements movements_to_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movements
    ADD CONSTRAINT movements_to_location_id_fkey FOREIGN KEY (to_location_id) REFERENCES public.locations(id) ON DELETE SET NULL;


--
-- Name: movements movements_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movements
    ADD CONSTRAINT movements_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: stock_containers stock_containers_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stock_containers
    ADD CONSTRAINT stock_containers_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id) ON DELETE RESTRICT;


--
-- Name: stock_containers stock_containers_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stock_containers
    ADD CONSTRAINT stock_containers_location_id_fkey FOREIGN KEY (location_id) REFERENCES public.locations(id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

\unrestrict ozhUFiuSfRikadCh8thF5B4skVim1K41p5e6fCWR1Zrm9yvPVQnA83BTF7mx77d

