import os
import hashlib
import qrcode
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_path", type=str, required=True)
    parser.add_argument("--message", type=str, required=True)
    args = parser.parse_args()

    image_dir = os.path.join(args.repo_path, "QRCodeGenerator", "images")
    if not os.path.exists(image_dir):
        os.mkdir(image_dir)

    message_md5 = hashlib.md5(args.message.encode("utf-8")).hexdigest()
    qr = qrcode.QRCode()
    qr.add_data(args.message)
    img = qr.make_image()
    img.save(os.path.join(image_dir, f"{message_md5}.png"))
    print(f"![](https://raw.githubusercontent.com/yym6472/LearnGitHubActions/master/QRCodeGenerator/images/{message_md5}.png)")


if __name__ == "__main__":
    main()