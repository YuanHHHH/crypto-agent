class CryptoAgentError(Exception):
    pass

class APIError(CryptoAgentError):
    """API 调用失败"""
    pass

class InvalidCoinError(CryptoAgentError):
    """无效的币种名称"""
    pass