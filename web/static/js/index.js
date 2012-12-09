var MARGIN = 100;
var TOP_MARGIN = 50;
var BOTTOM_MARGIN = 50;
var IMAGES = "http://placekitten.com/g/100/100"
var IMAGE_SIZE = 100;

// create a place for us to store important variables on the doc
var gibbs = {};

$(document).ready(function() {
    var pageHeight = document.height;
    var pageWidth = document.width;
    var game = $('#game');
    game.width(pageWidth - (MARGIN * 2))
        .height(pageHeight - TOP_MARGIN - BOTTOM_MARGIN);
    gameHeight= game.height();
    gameWidth = game.width();
    gibbs.game = game;
    gibbs.gameHeight = gameHeight;
    gibbs.gameWidth = gameWidth;

    loadImages();
});

/*
 * Function: loadImages
 * loads all images from server (or, as of now, from a given URL) and saves them
 * in the gibbs.images array
 */
function loadImages() {
    var i;
    gibbs.images = [];
    for (i = 0; i < 10; i++) {
        var newImage = new Image(IMAGES);
        newImage.addToScreen();
        gibbs.images.push(newImage);
    }
}

/*
 * Constructor: Image
 * Image class handles a single image.
 */
function Image(url) {
    this.url = url;
    this.x = Math.random() * (gibbs.gameWidth - IMAGE_SIZE);
    this.y = Math.random() * (gibbs.gameHeight - IMAGE_SIZE);
    this.object = $(document.createElement('img'));
    this.object.addClass('object')
    this.object.attr('src', url);
    this.object.css('left', this.x);
    this.object.css('top', this.y);
}

/*
 * Method: addToScreen
 * Adds the image to the dom
 *
 * Member Of: Image
 */
Image.prototype.addToScreen = function() {
    gibbs.game.append(this.object);
};
