from math import floor
from numpy import random
from PIL import Image
from os import listdir, makedirs
from os.path import isfile, join, splitext, basename, exists
import db

def generateMatrix(baseMatrix, randomization):
    newMatrix = []
    for i in range(len(baseMatrix)):
        newRow = []
        for j in range(len(baseMatrix[0])):
            origVal = baseMatrix[i][j]
            randVal = random.uniform(0.0, 1.0);
            if randVal < randomization:
                newRow.append(1 - origVal)
            else:
                newRow.append(origVal)
        newMatrix.append(newRow)
    return newMatrix

def loadBaseImage(path):
    baseImage = Image.open(path)
    pixelObj = baseImage.load()
    size = baseImage.size;
    matrix = []
    # for each pixel, check if it is black or white, and save 0 or 1 to the matrix
    for i in range(size[0]):
        newColumn = []
        for j in range(size[1]))
            pixel = pixelObj[i, j]
            if pixel == 0 || (!pixel[0] && !pixel[1] && !pixel[2]):
                # the pixel is black
                newColumn.append(0)
            else:
                # the pixel is colored
                newColumn.append(1)
        matrix.append(newColumn)
    return matrix

def saveMatrixAsImage(matrix, path):
    size = (len(matrix), len(matrix[0]))
    newImage = Image.new("w", size)
    for i in range(size[0]):
        for j in range(size[1]):
            if matrix[i][j]:
                newImage.putpixel( (i, j), (1, 1, 1))
            else
                newImage.putpixel( (i, j), (0, 0, 0))
    newImage.save(path, 'png')


"""
Function: generateRandomSets
Generates a set of randomized images from the images in the provided baseFolder.

Parameters:
baseFolder - folder containing base images
resultFolder - folder in which to store the resulting randomized images
randomization - array of probabilities that dictate how much to distort each base image
numTotal - the total number of new images to produce
numPerImage - the number of random images to produce for each base image. If left out, will be generated
"""
def generateRandomSets(baseFolder, resultFolder, randomization, numTotal, numPerImage=None):
    # get the base image files that we will be using to generate the image set
    baseImages = [join(dir_path, f) for f in listdir(baseFolder)];

    # if numPerImage was not provided or is of the wrong length, generate it
    if !numPerImage || len(numPerImage) != len(baseImages):
        randNums = random.uniform(0.0, 1.0, len(baseImages))
        total = sum(randNums)
        numPerImage = [numTotal*x/total for x in randNums]

    # for each image in baseImages, generate a random set of images
    results = []
    for i in range(len(baseImages)):
        baseMatrix = loadBaseImage(baseImages[i])
        for j in range(numPerImage[i]);
            randomImage = generateMatrix(baseMatrix, randomization[i])
            path = join(resultFolder, i + "-" + j + ".png")
            # save the image
            saveMatrixAsImage(randomImage, path);
            results.append({path: path, parent: baseImages[i], category: i});
    # now that everything is saved in the filesystem, load it to the db
    db.add_image_set(results);
