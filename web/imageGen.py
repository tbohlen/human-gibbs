from math import floor, ceil, exp, sqrt, pi
from numpy import random, zeros, convolve, transpose
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
def generateMatrix(baseMatrix, randomization, filterSize):
    newMatrix = []
    for i in range(len(baseMatrix)):
        newRow = []
        for j in range(len(baseMatrix[0])):
            origVal = baseMatrix[i][j]
            newRow.append(clamp(0, 255, random.normal(origVal, randomization)))
        newMatrix.append(newRow)
    return gaussianFilter(newMatrix, filterSize)

# downsamples to 5x5 chunks and randomizes
def generateImage(size, chunkSize, filterSize, sd=100):
    matrix = zeros([size, size])
    mean = random.uniform(0, 255)
    for i in range(int(size/chunkSize)):
        for j in range(int(size/chunkSize)):
            val = clamp(0, 255, random.normal(mean, sd))
            for m in range(chunkSize):
                for n in range(chunkSize):
                    matrix[i*chunkSize + m][j*chunkSize + n] = val
    return gaussianFilter(matrix, filterSize)

def generatePositionImage(size, chunkSize, filterSize, sd=100):
    matrix = zeros([size, size])
    mean = random.uniform(50, 205)
    #neg = random.uniform(0.0, 1.0)
    posMean = random.uniform(0, size/chunkSize, 2)
    for i in range(int(size/chunkSize)):
        for j in range(int(size/chunkSize)):
            dist = ( (i - posMean[0])**2 + (j - posMean[1]) ** 2 ) ** (0.1)
            val = clamp(0, 255, random.normal(mean/dist, sd))
            #if neg > 0.5:
            #val = 255-val
            for m in range(chunkSize):
                for n in range(chunkSize):
                    matrix[i*chunkSize + m][j*chunkSize + n] = val
    return gaussianFilter(matrix, filterSize)

def bwImage(size):
    matrix = zeros([size, size])
    white = int(floor(random.uniform(0.0, 2.0)))
    for i in range(int(size)):
        for j in range(int(size)):
            if white == 1.0:
                matrix[i][j] = 255
            else:
                matrix[i][j] = 0
    return matrix

# default values create a good group for testin
def generateBW(rootPath, num=40, size=100):
    for i in range(num):
        randomImage = bwImage(size)
        path = join(rootPath, str(i) + ".png")
        # save the image
        saveMatrixAsImage(randomImage, path)

    # now that everything is saved in the filesystem, load it to the db
    saved = False
    base = basename(rootPath)
    name = base
    number = 0
    while not saved:
        try:
            saved = True
            db.add_image_set(rootPath, name)
        except ValueError:
            name = base + str(number)
            number += 1
            saved = False
        except TypeError:
            saved = False
            raise
# default values create a good group for testin
def generateImages(rootPath, num=40, size=100, filterSize=15, chunkSize=10, sd=50, t="pos"):
    for i in range(num):
        if t == "pos":
            randomImage = generatePositionImage(size, chunkSize, filterSize, sd)
        else:
            randomImage = generateImage(size, chunkSize, filterSize, sd)
        path = join(rootPath, str(i) + ".png")
        # save the image
        saveMatrixAsImage(randomImage, path)

    # now that everything is saved in the filesystem, load it to the db
    saved = False
    base = basename(rootPath)
    name = base
    number = 0
    while not saved:
        try:
            saved = True
            db.add_image_set(rootPath, name)
        except ValueError:
            name = base + str(number)
            number += 1
            saved = False
        except TypeError:
            saved = False
            raise

# bounds value so that it is not larger than high and no smaller than low
def clamp(low, high, val):
    if high < val:
        return high
    if low > val:
        return low
    return val

# returns the value of the gaussian with the given mean and standard dev at the given point
def gaussianValue(mean, sd, x):
    exponent = -1 * pow( (x - mean), 2) / (2 * sd * sd)
    return exp(exponent) / (sqrt(2 * pi * sd * sd))

# returns a set of discrete values sampled at evenly spaced locations on a gaussian
def discreteGaussian(num, mean=0.5, sd=0.2):
    return [gaussianValue(mean, sd, float(x+1)/(num+1)) for x in range(int(num))]

def gaussianFilter(matrix, filterSize):
    # filters the images using a gaussian
    size = (len(matrix), len(matrix[0]))
    xFilterMatrix = zeros(size)
    yFilterMatrix = zeros(size)
    kernel = discreteGaussian(filterSize)
    kernelSum = sum(kernel)

    # blur columns
    for i in range(size[0]):
        xFilterMatrix[i] = [x/kernelSum for x in convolve(matrix[i], kernel, "same")]

    xFilterMatrix = transpose(xFilterMatrix)

    # blur rows
    for j in range(size[0]):
        yFilterMatrix[j] = [x/kernelSum for x in convolve(xFilterMatrix[j], kernel, "same")]

    return transpose(yFilterMatrix)


"""
Function: loadImage
loads an image from the path provided. Downsamples by a factor of 9 to make images large enough to be viewed by humans. Any 3x3 square containing more dark than light is black, and vise versa.

Parameters:
path - the path to the image to be loaded
downsample - an integer indicating how much to downsample the image. A value of 1 indicates no downsampling
"""
def loadImage(path, downsample=1):
    baseImage = Image.open(path)
    pixelObj = baseImage.load()
    size = baseImage.size
    matrix = []
    # for each pixel, check if it is black or white, and save 0 or 1 to the matrix in the appropriate place
    for i in range(size[0]):
        newColumn = []
        for j in range(size[1]):
            # converts to gray-scale, just in case
            pixel = pixelObj[i, j]
            if baseImage.mode == "1":
                newColumn.append(pixel)
            else:
                newColumn.append(sum(pixelObj[i, j])/3.0) # we are not dealing with grayscale, but instead a color image
        matrix.append(newColumn)

    # downsample, if required
    # this is messy. if downsample does not divide the image size, the extra pixels are just thrown away
    # TODO: fix the above error
    downsampleMatrix = []
    if downsample > 1:
        for i in range(int(floor(size[0]/downsample))):
            newColumn = []
            for j in range(int(floor(size[1]/downsample))):
                pixelSum = 0
                for k in range(downsample):
                    for l in range(downsample):
                        pixelSum += matrix[i*downsample+k][j*downsample+l]
                newColumn.append(int(floor(pixelSum/(downsample**2))))
            downsampleMatrix.append(newColumn)
    else:
        downsampleMatrix = matrix

    return downsampleMatrix

"""
Function: saveMatrixAsImage
Saves a black and white image file generated from the provided matrix at the specified path. Upsamples the image by a factor of 9 (9 pixels per matrix entry)

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
randomization - probability that dictate how much to distort each base image
numTotal - the total number of new images to produce
numPerImage - the number of random images to produce for each base image. If left out, will be generated
"""
def generateRandomSets(baseFolder, resultFolder, randomization, numTotal, filterSize=10, numPerImage=None):
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
            randomImage = generateMatrix(baseMatrix, randomization, filterSize)
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
