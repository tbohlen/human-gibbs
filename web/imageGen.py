from math import floor, ceil, exp, sqrt, pi
from numpy import random, zeros
from PIL import Image
from os import listdir
from os.path import join, basename, normpath, normpath
import db

"""
Function: generateMatrix
Generates a randomized matrix based on the input image.

This samples from a gaussian for each pixel. The mean of the gaussian is the original pixel value, and the standard dev is randomization

Parameters:
baseMatrix - the matrix to randomize to produce the new matrix
randomization - the probability of flipping each bit
"""
def generateMatrix(baseMatrix, randomization):
    newMatrix = []
    for i in range(len(baseMatrix)):
        newRow = []
        for j in range(len(baseMatrix[0])):
            origVal = baseMatrix[i][j]
            newRow.append(clamp(0, 255, random.normal(origVal, randomization)))
        newMatrix.append(newRow)
    return gaussianFilter(newMatrix)

# bounds value so that it is not larger than high and no smaller than low
def clamp(low, high, val):
    if high < val:
        return high
    if low > val:
        return low
    return val

# returns the value of the gaussian with the given mean and standard dev at the given point
#def gaussianValue(mean, sd, x):
    #exponent = -1 * pow( (x - mean), 2) / (2 * sd * sd)
    #return exp(exponent) / (sqrt(2 * pi * sd * sd))

def gaussianFilter(matrix):
    # filters the images using a gaussian
    size = (len(matrix), len(matrix[0]))
    xFilterMatrix = zeros(size)
    yFilterMatrix = zeros(size)
    k = [0.1201, 0.2339, 0.2931, 0.2339, 0.1201];
    for i in range(size[0]):
        for j in range(size[1]):
            total = 0
            for m in range(5):
                x = clamp(0, size[0]-1, i+m-2)
                total += k[m] * matrix[x][j]
            xFilterMatrix[i][j] = total

    for i in range(size[0]):
        for j in range(size[1]):
            total = 0
            for n in range(5):
                y = clamp(0, size[0]-1, j+n-2)
                total += k[n] * xFilterMatrix[i][y]
            yFilterMatrix[i][j] = total
    return yFilterMatrix


"""
Function: loadImage
loads an image from the path provided. Downsamples by a factor of 9 to make images large enough to be viewed by humans. Any 3x3 square containing more dark than light is black, and vise versa.

Parameters:
path - the path to the image to be loaded
"""
def loadImage(path):
    baseImage = Image.open(path)
    pixelObj = baseImage.load()
    size = baseImage.size
    matrix = []
    # for each pixel, check if it is black or white, and save 0 or 1 to the matrix in the appropriate place
    for i in range(size[0]):
        newColumn = []
        for j in range(size[1]):
            # converts to gray-scale, just in case
            newColumn.append(sum(pixelObj[i, j])/3.0)
        matrix.append(newColumn)
    return matrix

"""
Function: saveMatrixAsImage
Saves a black and white image file generated from the provided matrix at the specified path. Updamples the image by a factor of 9 (9 pixels per matrix entry)

Parameters:
matrix - the matrix of values (1s and 0s) to be converted to an image
path - the path at which to save the image
"""
def saveMatrixAsImage(matrix, path):
    size = (len(matrix), len(matrix[0]))
    newImage = Image.new("RGB", size)
    for i in range(size[0]):
        for j in range(size[1]):
            # for each entry in the matrix
            val = int(matrix[i][j])
            newImage.putpixel((i, j), (val, val, val))

    newImage.save(path, 'PNG')


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
    normpath(baseFolder) # i think this should take care of trailing separators for the name gen below
    baseImages = [join(baseFolder, f) for f in listdir(baseFolder)]
    baseImages = filter(db.is_image, baseImages)

    # if numPerImage was not provided or is of the wrong length, generate it
    if not numPerImage or len(numPerImage) != len(baseImages):
        randNums = random.uniform(0.0, 1.0, len(baseImages))
        total = sum(randNums)
        numPerImage = [numTotal*x/total for x in randNums]

    # for each image in baseImages, generate a random set of images
    results = []
    for i in range(len(baseImages)):
        baseMatrix = loadImage(baseImages[i])
        for j in range(numPerImage[i]):
            randomImage = generateMatrix(baseMatrix, randomization[i])
            path = join(resultFolder, str(i) + "-" + str(j) + ".png")
            # save the image
            saveMatrixAsImage(randomImage, path)
            results.append({'path': path, 'parent': baseImages[i], 'category': i})

    # now that everything is saved in the filesystem, load it to the db
    saved = False
    base = basename(baseFolder)
    name = base
    number = 0
    while not saved:
        try:
            saved = True
            db.add_image_set_by_array(results, baseImages, name)
        except ValueError:
            name = base + str(number)
            number += 1
            saved = False
        except TypeError:
            saved = False
            raise
