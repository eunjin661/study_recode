from fastmcp import FastMCP
mcp = FastMCP(name='calculator')

@mcp.tool()
def get_greeting(name:str) -> str:
    return f'안녕하세요 {name}님 mcp 서버에 오신것을 환영합니다!'

@mcp.tool()
def multiply(a:float, b:float)->float:
    '''Multiplies two numbers together.'''
    return a*b

if __name__ == '__main__':
    mcp.run()

# 실행은 uv run server.py
