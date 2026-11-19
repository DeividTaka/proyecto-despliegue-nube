#!/bin/bash
URL=${1:-"http://localhost"}

echo "=== 1. Verificando Salud y Balanceo de Cargas ==="
for i in {1..4}; do
  curl -s "$URL/api/status"
  echo ""
done

echo -e "\n=== 2. Probando Inserción en Base de Datos ==="
curl -s -X POST "$URL/api/tareas" \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Prueba automatizada de liberación"}'
echo -e "\n"