import MetaTrader5 as mt5

def connect(symbol_to_check="XAUUSD"):
    if not mt5.initialize():
        raise RuntimeError(f"No se pudo conectar con MT5: {mt5.last_error()}")
    print("✅ Conexión establecida con MetaTrader 5")

    # Validar que el símbolo esté habilitado
    symbol_info = mt5.symbol_info(symbol_to_check)
    if symbol_info is None or not symbol_info.visible:
        if not mt5.symbol_select(symbol_to_check, True):
            raise RuntimeError(f"No se pudo habilitar el símbolo '{symbol_to_check}'")
        else:
            print(f"🔎 Símbolo '{symbol_to_check}' habilitado para trading.")

def disconnect():
    mt5.shutdown()
    print("🔌 Conexión cerrada")
