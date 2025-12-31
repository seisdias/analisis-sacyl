# app/main.py
import logging
from app import AnalisisSACYLApp


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = AnalisisSACYLApp()
    app.mainloop()


if __name__ == "__main__":
    main()
