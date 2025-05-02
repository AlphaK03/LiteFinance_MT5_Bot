import MetaTrader5 as mt5

def connect():
    if not mt5.initialize():
        raise RuntimeError(f"No se pudo conectar con MT5: {mt5.last_error()}")
    print("✅ Conexión establecida con MetaTrader 5")

def disconnect():
    mt5.shutdown()
    print("🔌 Conexión cerrada")
