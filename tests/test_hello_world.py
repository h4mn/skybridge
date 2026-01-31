"""
Teste hello-world para issue #999
Este é um teste simples do skill hello-world
"""


def test_hello_world():
    """Teste básico hello-world"""
    message = "Hello, World!"
    assert message == "Hello, World!"
    assert len(message) > 0
    assert "World" in message


def test_hello_world_uppercase():
    """Teste hello-world em maiúsculas"""
    message = "Hello, World!".upper()
    assert message == "HELLO, WORLD!"


def test_hello_world_contains():
    """Teste se hello-world contém palavras esperadas"""
    message = "Hello, World!"
    assert "Hello" in message
    assert "World" in message
