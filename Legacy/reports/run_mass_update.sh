#!/bin/bash

# Script para ejecutar actualización masiva por lotes
# Procesa de 1 a 36,645,703 en lotes de 10,000

echo "🚀 INICIANDO ACTUALIZACIÓN MASIVA POR LOTES"
echo "=============================================="

# Configuración
BATCH_SIZE=10000
START_ID=1
END_ID=36645703
CURRENT_ID=$START_ID
BATCH_NUM=1
TOTAL_BATCHES=$(((END_ID - START_ID + BATCH_SIZE - 1) / BATCH_SIZE))

echo "📊 Configuración:"
echo "   - Rango total: $START_ID - $END_ID"
echo "   - Tamaño lote: $BATCH_SIZE"
echo "   - Total lotes: $TOTAL_BATCHES"
echo "   - Tiempo estimado: $((TOTAL_BATCHES * 30 / 60)) minutos"
echo ""

# Función para ejecutar lote
execute_batch() {
    local start=$1
    local end=$2
    local batch_num=$3
    
    echo "🔄 Lote $batch_num/$TOTAL_BATCHES: IDs $start-$end"
    
    # Ejecutar lote
    docker-compose exec postgres psql -U sms_user -d sms_marketing -c "
        SELECT 'Lote $batch_num ($start-$end)' as mensaje;
        SELECT * FROM update_contacts_batch($start, $end);
    " 2>/dev/null
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ Lote $batch_num completado"
    else
        echo "❌ Error en lote $batch_num"
        return 1
    fi
    
    return 0
}

# Función para mostrar progreso
show_progress() {
    echo ""
    echo "📈 PROGRESO ACTUAL:"
    docker-compose exec postgres psql -U sms_user -d sms_marketing -c "
        SELECT * FROM get_update_progress();
    " 2>/dev/null
    echo ""
}

# Procesar lotes
while [ $CURRENT_ID -le $END_ID ]; do
    BATCH_END=$((CURRENT_ID + BATCH_SIZE - 1))
    
    # Ajustar último lote
    if [ $BATCH_END -gt $END_ID ]; then
        BATCH_END=$END_ID
    fi
    
    # Ejecutar lote
    execute_batch $CURRENT_ID $BATCH_END $BATCH_NUM
    
    if [ $? -ne 0 ]; then
        echo "❌ Error en lote $BATCH_NUM. Continuando..."
    fi
    
    # Mostrar progreso cada 100 lotes
    if [ $((BATCH_NUM % 100)) -eq 0 ]; then
        show_progress
    fi
    
    # Pausa pequeña
    sleep 2
    
    # Siguiente lote
    CURRENT_ID=$((BATCH_END + 1))
    BATCH_NUM=$((BATCH_NUM + 1))
done

echo ""
echo "🎊 ACTUALIZACIÓN MASIVA COMPLETADA"
echo "=================================="

# Mostrar progreso final
show_progress

# Verificar resultados
echo "🔍 VERIFICACIÓN FINAL:"
docker-compose exec postgres psql -U sms_user -d sms_marketing -c "
    SELECT * FROM verify_ift_update();
" 2>/dev/null

echo ""
echo "✅ Proceso completado. Revisa los resultados arriba."