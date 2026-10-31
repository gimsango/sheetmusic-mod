

# ============================================================================
#  [PC] 진입점
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
        elif a == '--fullscreen':
            args['fullscreen'] = True
        elif a == '--offscreen':
            args['offscreen'] = True
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
    args = parse_args(sys.argv)
    if args.get('serve'):
        serve_forever(args.get('port', DEFAULT_PORT))
        return
    game = Game(args)
    try:
        game.run()
    finally:
        try:
            game.profile.save()
            game.session.leave()
        except Exception:
            pass


if __name__ == '__main__':
    main()
