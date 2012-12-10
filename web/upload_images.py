import argparse
import db

parser = argparse.ArgumentParser(description='Upload a directory of image files as an image set')
parser.add_argument('dir', help='The directory to upload')

if __name__ == '__main__':
    args = parser.parse_args()

    db.add_image_set(args.dir)
