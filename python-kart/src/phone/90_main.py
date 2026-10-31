

# ============================================================================
#  [폰] 진입점
# ============================================================================
def parse_args(argv):
    args = {}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == '--serve':
            args['serve'] = True
        elif a == '--fps':
            args['fps'] = True
        elif a == '--window' and i + 1 < len(argv):
            i += 1
            try:
                w, h = argv[i].lower().split('x')
                args['window'] = (int(w), int(h))
            except ValueError:
                pass
        elif a == '--lang' and i + 1 < len(argv):
            i += 1
            args['lang'] = argv[i]
        elif a == '--port' and i + 1 < len(argv):
            i += 1
            try:
                args['port'] = int(argv[i])
            except ValueError:
                pass
        i += 1
    return args


def main():
    try:
        args = parse_args(sys.argv)
        if args.get('serve'):
            serve_forever(args.get('port', DEFAULT_PORT))
            return
        app = App(args)
        app.run()
    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException:
        import traceback
        text = traceback.format_exc()
        print(text)
        path = _crash_log(text)
        print('=' * 64)
        print('오류가 발생했습니다. 위의 내용을 그대로 알려주세요.  /  An error occurred. Please send the text above.')
        if path:
            print('(같은 내용이 파일로도 저장되었습니다 / also saved to: %s)' % path)
        print('=' * 64)
        _wait_key()
        raise SystemExit(1)


if __name__ == '__main__':
    main()
