# Warehouse18 – Inventory & Asset Management (RFID-ready)

Warehouse18 es un sistema de gestión de inventario diseñado para **entornos reales**:  
almacenes con **activos serializados**, **consumibles por cantidad**, **barcodes compartidos por pack**, **RFID**, y **integraciones externas inestables** (APIs, red, etc.).

El modelo prioriza:
- consistencia de datos
- trazabilidad completa
- tolerancia a fallos
- y separación clara entre dominio, estado e integración

---

## 🧠 Principios de diseño

- **Activos ≠ Consumibles**
  - Los activos serializados se gestionan **unidad a unidad**
  - Los consumibles se gestionan **por cantidad**
- **Un barcode no siempre identifica una unidad**
  - En consumibles, el barcode identifica un **contenedor/pack**
- **El sistema no depende de APIs externas para funcionar**
- **Nada se pierde si no hay internet**
- **Todo lo que pasa queda registrado**

---

## 🧩 Conceptos clave del dominio

### Items
Representan el **tipo de cosa** (ej. *Tablet*, *Tornillos M4*).

Campos clave:
- `is_serialized`
- `uom` (unit of measure)
- `min_stock`, `reorder_point`

---

### Assets (solo para items serializados)
Representan **unidades físicas individuales**.

- 1 asset = 1 EPC / barcode
- No existen assets para consumibles

---

### Stock Containers (packs de consumibles)
Representan **cajas/bolsas/lotes** de consumibles con un único barcode.

- 1 barcode → N unidades dentro
- La cantidad se descuenta con el uso
- No convierten el consumible en asset

---

### Inventory Stock
Estado derivado del stock **por item y ubicación**.

- Para consumibles: cantidad real
- Para activos: opcional (normalmente se deriva por conteo)

---

### Movements
Registro inmutable de **todo lo que ocurre**:

- GR (Goods Receipt)
- GI (Goods Issue)
- GT (Goods Transfer)
- ADJ (Adjustment)
- INFO (movimientos informativos)

Soporta:
- movimientos por cantidad
- movimientos por assets
- cambios de ubicación
- referencias a assets o contenedores

---

### Asset Enrichment
Capa opcional para **datos externos** (ej. serial number desde una API).

- No bloquea operaciones
- Tiene estado (`pending`, `ok`, `error`, etc.)
- Controla reintentos

---

### Integration Outbox
Implementa el **Transactional Outbox Pattern**.

- Registra eventos pendientes de enviar a sistemas externos
- Funciona incluso sin conexión
- Reintentos controlados
- No usa foreign keys (referencias polimórficas)

---

### Audit & Error Logs
Observabilidad completa:

- `audit_log`: quién hizo qué y cuándo
- `error_log`: qué falló, por qué y si está resuelto

---

## 🗄️ Base de datos

- **PostgreSQL**
- Integridad garantizada con:
  - PK / FK
  - `CHECK` constraints
  - `UNIQUE`
  - triggers de negocio
- Separación clara entre:
  - dominio
  - estado derivado
  - integración
  - observabilidad

---

## 🔒 Reglas de negocio (en resumen)

- Un item serializado **no puede** tener stock containers
- Un item no serializado **no debe** tener assets
- Un movimiento por assets **no puede mezclar items**
- Un contenedor con `quantity = 0` pasa automáticamente a `empty`
- EPC / barcode de assets **no se reutiliza nunca**
- La outbox **no depende** de la existencia de la entidad original

Las reglas se aplican en:
- Base de datos (constraints / triggers)
- Aplicación
- Documentación (`docs/business_rules.md`)

---

## 🛠️ Tecnologías

- PostgreSQL
- RFID / Barcode ready
- API-first friendly
- Pensado para workers asíncronos y sistemas distribuidos

---

## 📌 Estado del proyecto

- Modelo de datos definido y validado
- DDL PostgreSQL completo
- Triggers de negocio implementados
- Listo para implementación de backend

---

## 📄 Licencia

Uso interno / proyecto privado (ajustar según necesidad).

---

## 💬 Nota final

Este sistema está diseñado para **no romperse cuando el mundo real se comporta mal**:
red caida, APIs lentas, usuarios humanos y procesos imperfectos.

Si algo parece “más complejo de lo normal”, probablemente es porque evita
un problema que ya ha ocurrido en producción alguna vez.