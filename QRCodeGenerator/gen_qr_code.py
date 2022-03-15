import qrcode
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", type=str, default="")
    args = parser.parse_args()

    message = args.message
    qr = qrcode.QRCode()
    qr.add_data(message)
    img = qr.make_image()
    img.save("test.png")


if __name__ == "__main__":
    main()