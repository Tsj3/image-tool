"""支持通过 ``python -m image_tool`` 运行。"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
