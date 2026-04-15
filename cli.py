"""CLI 入口点"""
import sys
import argparse


def main(args=None):
    """主入口函数"""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description='aitext CLI')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # serve 命令
    serve_parser = subparsers.add_parser('serve', help='启动 API 服务器')
    serve_parser.add_argument('--host', default='127.0.0.1', help='监听地址')
    serve_parser.add_argument('--port', type=int, default=8005, help='监听端口')
    serve_parser.add_argument('--reload', action='store_true', help='开启热重载')

    parsed_args = parser.parse_args(args)

    if parsed_args.command == 'serve':
        import uvicorn
        from .interfaces.main import app

        uvicorn.run(
            app,
            host=parsed_args.host,
            port=parsed_args.port,
            reload=parsed_args.reload
        )
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
