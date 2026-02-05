# warehouse18

Warehouse 18 inventory control (entries/exits/movements) with sync to a remote API.

@startuml
hide circle
skinparam linetype ortho
skinparam classAttributeIconSize 0

' =========================
' Core catalog / master data
' =========================
class users {
  +id (PK)
  username (UNIQUE)
  full_name
  email (UNIQUE, NULL)
  role
  department (NULL)
  is_active
  password_hash (NULL)
  auth_provider
  last_login_at (NULL)
  created_at
  updated_at
}

class items {
  +id (PK)
  name
  description (NULL)
  category (NULL)
  uom
  is_serialized
  min_stock
  reorder_point
  is_active
  created_at
  updated_at
}

class assets {
  +id (PK)
  asset_code (UNIQUE)  ' barcode = EPC
  item_id (FK, NULL)
  status
  created_at
  updated_at
}

class locations {
  +id (PK)
  code (UNIQUE)
  name
  type
  parent_id (FK, NULL)
  is_active
}

' =========================
' Integration / outbox (polymorphic)
' =========================
class integration_outbox {
  +id (PK)
  direction           ' outbound
  target_system       ' external_api
  entity_type         ' asset, movement, container, etc
  entity_id           ' polymorphic reference (NOT a FK)
  action              ' push_update, notify_move...
  payload_json
  status              ' pending, sent, error
  retries
  last_attempt_at (NULL)
  next_retry_at (NULL)
  created_at
}

' =========================
' Current-state tables (derived)
' =========================
class inventory_stock {
  +id (PK)
  item_id (FK)
  location_id (FK)
  quantity
  updated_at
}

class asset_location {
  +asset_id (PK/FK)
  location_id (FK)
  since
}

' =========================
' Movements (event log)
' =========================
class movement_types {
  +id (PK)
  code (UNIQUE)  ' GR, GI, GT, ADJ, INFO
  name
  affects_stock
  affects_location
  stock_sign  ' +1, -1, 0
}

class movements {
  +id (PK)
  movement_type_id (FK)
  item_id (FK, NULL)
  quantity
  from_location_id (FK, NULL)
  to_location_id (FK, NULL)
  reference_type (NULL)  ' asset | container | other
  reference_id (NULL)    ' polymorphic reference (NOT a FK)
  user_id (FK, NULL)
  created_at
  notes (NULL)
}

class movement_assets {
  +movement_id (PK/FK)
  +asset_id (PK/FK)
}

' =========================
' Consumable containers
' =========================
class stock_containers {
  +id (PK)
  container_code (UNIQUE)   ' barcode del pack/caja
  item_id (FK)
  location_id (FK)
  quantity
  status                    ' open, empty, discarded
  created_at
  updated_at
}

' =========================
' Observability / audit / errors
' =========================
class audit_log {
  +id (PK)
  at
  user_id (FK, NULL)
  action
  entity_type
  entity_id
  before_json (NULL)
  after_json (NULL)
  request_id (NULL)
}

class error_log {
  +id (PK)
  happened_at
  severity
  source
  operation (NULL)
  entity_type (NULL)
  entity_id (NULL)
  user_id (FK, NULL)
  request_id (NULL)
  message
  exception_type (NULL)
  stacktrace (NULL)
  metadata_json (NULL)
  resolved_at (NULL)
  resolved_by (FK, NULL)
  resolution_notes (NULL)
}

class asset_enrichment {
  +asset_id (PK/FK)
  serial_number (NULL)
  sync_status
  last_sync_at (NULL)
  last_error (NULL)
  retries
}

' =========================
' Relationships
' =========================

' items <-> assets
items "1" <-- "0..*" assets : item_id

' items <-> stock containers
items "1" <-- "0..*" stock_containers : item_id

' locations hierarchy
locations "0..1" <-- "0..*" locations : parent_id

' inventory stock
items "1" <-- "0..*" inventory_stock : item_id
locations "1" <-- "0..*" inventory_stock : location_id

' asset current location
assets "1" <-- "0..1" asset_location : asset_id
locations "1" <-- "0..*" asset_location : location_id

' stock container current location
locations "1" <-- "0..*" stock_containers : location_id

' movement types & movements
movement_types "1" <-- "0..*" movements : movement_type_id

' movements reference locations
locations "1" <-- "0..*" movements : from_location_id
locations "1" <-- "0..*" movements : to_location_id

' movements reference user
users "1" <-- "0..*" movements : user_id

' movements <-> assets
movements "1" <-- "0..*" movement_assets : movement_id
assets "1" <-- "0..*" movement_assets : asset_id

' movements may reference item (qty-based)
items "1" <-- "0..*" movements : item_id

' audit/error logs
users "1" <-- "0..*" audit_log : user_id
users "1" <-- "0..*" error_log : user_id
users "1" <-- "0..*" error_log : resolved_by

' enrichment
assets "1" <-- "0..1" asset_enrichment : asset_id

' NOTE: integration_outbox.entity_type/entity_id are polymorphic references
' so we do NOT model them as FK relationships in the UML.

@enduml
