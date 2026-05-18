import sys

line = sys.stdin.readline()

if line is None or line == '':
    print('n/a')
else:
    try:
        x = int(line)
        if x < 1000:
            print(x)
        else:
            print(f'{x / 1000:.1f}k')
    except ValueError:
        print('n/a')
