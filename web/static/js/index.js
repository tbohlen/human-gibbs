var MARGIN = 125;
var TOP_MARGIN = 50;
var BOTTOM_MARGIN = 50;
var IMAGES = "http://placekitten.com/g/100/100"
var IMAGE_SIZE = 102;
var GROUP_MARGIN = 10;
var GROUP_ROW = 4;
var GROUP_COL = 2;

// create a place for us to store important variables on the doc
var gibbs = {};
gibbs.dragObj = null;
gibbs.lastMousePos = [0, 0];
gibbs.nextImage = 0;

/*
 * Function: cancel
 * Cancels an event to prevent it from triggering further handlers. _almost_
 * foolproof.
 *
 * Parameters:
 * ev - the event to be canceled
 *
 * Returns:
 * Always returns false. This value should be returned from the calling handler,
 * too.
 */
function cancel(ev) {
    if (ev.preventDefault) {
        ev.preventDefault();
    }
    ev.returnValue = false;
    if (ev.stopPropagation) {
        ev.stopPropagation();
    }
    if (ev.stopImmediatePropagation) {
        ev.stopImmediatePropagation();
    }
    ev.cancelBubble = true;
    return false;
}

/*
 * Function: clamp
 * Clamps the value provided between high and low
 */
function clamp(low, high, val) {
    if (high < val) {
        return high;
    }
    else if (low > val) {
        return low;
    }
    return val;
}

/*
 * Function: objectForID
 * Returns the object, whether group of image, for the given ID.
 */
function objectForID(gibbsID) {
    var regex = /^g.+/;
    if (regex.exec(gibbsID)) {
        var index = parseInt(gibbsID.substr(1), 10);
        return gibbs.groups[index];
    }
    else {
        var index = parseInt(gibbsID, 10);
        return gibbs.images[index];
    }
}

/*
 * Function: gamePosition
 * returns the x and y position relative to the game
 *
 * Parameters:
 * absPos - x and y positions relative to the page
 */
function gamePosition(absPos) {
    var offsetX = gibbs.game.offset().left;
    var offsetY = gibbs.game.offset().top;
    return [absPos[0] - offsetX, absPos[1] - offsetY];
}

/*
 * Function: getGroup
 * Determines if the position is within a group, and, if so, returns the group
 * index in gibbs.groups.
 */
function getGroup(pos) {
    var i;
    for (i = 0; i < gibbs.groups.length; i++) {
        var group = gibbs.groups[i];
        if (group.pointInside(pos)) {
            return group.id;
        }
    }
    return -1;
}

/*
 * Function: loadImages
 * loads all images from server (or, as of now, from a given URL) and saves them
 * in the gibbs.images array
 */
function loadImages() {
    var i;
    gibbs.images = [];
    for (i = 0; i < 10; i++) {
        var newImage = new Image(IMAGES, gibbs.game, i.toString());
        gibbs.images.push(newImage);
    }
}

/*
 * Function: loadGroups
 * Creates the first group on screen
 */
function loadGroups() {
    gibbs.groups = [];
    var newGroup = new Group([GROUP_MARGIN/2, GROUP_MARGIN/2], gibbs.groupSize, "g0");
    newGroup.addToScreen();
    gibbs.groups.push(newGroup);
}

/*
 * Function: warn
 * Warns the player they can't do that
 */
function warn(text) {
    var warning = $('#warning')
    warning.css('top', (document.height - warning.height())/2);
    warning.css('left', (document.width - warning.width())/2);
    $('#warningText').text(text);
    warning.show();
}

/*
 * Function: showImage
 * Shows the next image in the next image area.
 */
function showImage() {
    if (gibbs.nextImage < gibbs.images.length) {
        $('#noMoreImages').show();
    }
    var image = gibbs.images[gibbs.nextImage];
    image.moveTo([-116, 30]);
    image.addToScreen();
    gibbs.nextImage++;
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////// Image Object ////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

/*
 * Constructor: Image
 * Image class handles a single image.
 */
function Image(url, container, id) {
    this.url = url;
    this.id = id;
    var x = Math.random() * (container.innerWidth() - IMAGE_SIZE);
    var y = Math.random() * (container.innerHeight() - IMAGE_SIZE);
    this.pos = [x, y];
    this.unstaged = false;

    // is the last known "ok" position of the object
    // generally this means it
    this.lastSolidPos = [x, y];
    // the pos if we were following the mouse perfectly. Saved to have nice
    // behavior when user tries to drag out of the game
    this.perfectPos = [x, y];

    this.object = $(document.createElement('img'));
    this.object.addClass('image')
    this.object.attr('src', url);
    this.object.css('left', this.pos[0]);
    this.object.css('top', this.pos[1]);
    this.object.data('gibbsID', this.id);
    this.object.css('z-index', 2);
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

/*
 * Method: move
 * Moves the object by the number of pixels given
 *
 * Parameters:
 * delta - the move delta to be applies. Array of x, y.
 *
 * Member Of: Image
 */
Image.prototype.move = function(delta) {
    var newPos = [this.perfectPos[0] + delta[0], this.perfectPos[1] + delta[1]];
    this.perfectPos = [newPos[0], newPos[1]];
    
    if (this.unstaged) {
        this.pos[0] = clamp(0, gibbs.game.innerWidth() - IMAGE_SIZE - 1, this.perfectPos[0]);
        this.pos[1] = clamp(0, gibbs.game.innerHeight() - IMAGE_SIZE - 1, this.perfectPos[1]);
    }
    else {
        this.pos[0] = this.perfectPos[0];
        this.pos[1] = this.perfectPos[1];
    }
    this.object.css('left', this.pos[0]);
    this.object.css('top', this.pos[1])
};

/*
 * Method: moveTo
 * Moves the image to the new game location
 *
 * Parameters:
 * newPos - the new game position of the image as an array of x, y
 *
 * Member Of: Image
 */
Image.prototype.moveTo = function(newPos) {
    this.perfectPos = [newPos[0], newPos[1]];
    if (this.unstaged) {
        this.pos[0] = clamp(0, gibbs.game.innerWidth() - IMAGE_SIZE - 1, this.perfectPos[0]);
        this.pos[1] = clamp(0, gibbs.game.innerHeight() - IMAGE_SIZE - 1, this.perfectPos[1]);
    }
    else {
        this.pos[0] = this.perfectPos[0];
        this.pos[1] = this.perfectPos[1];
    }
    this.object.css('left', this.pos[0]);
    this.object.css('top', this.pos[1])
};

/*
 * Method: startDrag
 * handles the beginning of a drag
 *
 * Parameters:
 * ev - the event that started the drag
 * pos - the game position of the mouse when the event fired
 *
 * Member Of: Image
 */
Image.prototype.startDrag = function(ev, pos) {
    this.lastSolidPos = [this.pos[0], this.pos[1]];
    this.object.addClass('dragImage');
};

/*
 * Method: endDrag
 * Handles the ending of a drag
 *
 * Parameters:
 * ev - the event that ended the drag
 * pos - the game position of the mouse when the event fired
 *
 * Member Of: Image
 */
Image.prototype.endDrag = function(ev, pos) {
    var groupID = getGroup(pos);
    if (groupID == -1) {
        this.moveTo(this.lastSolidPos);
    }
    else {
        // if not unstaged, mark as unstaged and stage next
        if (!this.unstaged) {
            this.unstaged = true;
            showImage();
        }
        // modify the position so that it is inside the group
        var group = objectForID(groupID);
        console.log("before is " + this.perfectPos[0] + ", " + this.perfectPos[1]);
        this.perfectPos[0] = clamp(group.pos[0], group.pos[0] + group.size[0] - IMAGE_SIZE - 1, this.perfectPos[0]);
        this.perfectPos[1] = clamp(group.pos[1], group.pos[1] + group.size[1] - IMAGE_SIZE - 1, this.perfectPos[1]);
        this.moveTo(this.perfectPos);
        this.lastSolidPos = [this.pos[0], this.pos[1]];

        // TODO: save data!
    }
    this.object.removeClass('dragImage');
};

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////// Group Object ////////////////////////////////
///////////////////////////////////////////////////////////////////////////////


/*
 * Constructor: Group
 * Builds a new group
 */
function Group(startPos, startSize, id) {
    this.pos = startPos;
    this.size = startSize;
    this.id = id;

    // is the last known "ok" position of the object
    // generally this means it
    this.lastSolidPos = startPos;
    // the pos if we were following the mouse perfectly. Saved to have nice
    // behavior when user tries to drag out of the game
    this.perfectPos = startPos;

    this.object = $(document.createElement('div'));
    this.object.addClass('group')
    this.object.css('left', this.pos[0]);
    this.object.css('top', this.pos[1]);
    this.object.width(this.size[0]);
    this.object.height(this.size[1]);
    this.object.data('gibbsID', this.id);
    this.object.css('z-index', 1);
}

/*
 * Method: addToScreen
 * Adds the image to the dom
 *
 * Member Of: Group
 */
Group.prototype.addToScreen = function() {
    gibbs.game.append(this.object);
};

/*
 * Method: pointInside
 * Checks to see if point is inside the shape
 *
 * Parameters:
 * point - the point to test for, an array of x, y in game coordinates
 *
 * Returns:
 * True if the point is in the group, false otherwise.
 *
 * Member Of: Group
 */
Group.prototype.pointInside = function(point) {
    return (point[0] > this.pos[0] && point[0] < this.pos[0] + this.size[0]
        && point[1] > this.pos[1] && point[1] < this.pos[1] + this.size[1]);
};

///////////////////////////////////////////////////////////////////////////////
/////////////////////////// Doc Ready Event Handler ///////////////////////////
///////////////////////////////////////////////////////////////////////////////

/*
 * Loads page on 'ready' event
 */
$(document).ready(function() {
    var pageHeight = document.height;
    var pageWidth = document.width;
    var game = $('#game');
    game.width(pageWidth - (MARGIN * 2))
        .height(pageHeight - TOP_MARGIN - BOTTOM_MARGIN);
    gameHeight = game.height();
    gameWidth = game.width();
    gibbs.game = game;
    gibbs.gameHeight = gameHeight;
    gibbs.gameWidth = gameWidth;

    gibbs.groupSize = [(gameWidth/4) - GROUP_MARGIN, (gameHeight/2) - GROUP_MARGIN];


    loadImages();
    loadGroups();
    showImage();

    // attach handlers
    
    gibbs.game.on('mousedown', '.image', function(ev) {
        // claim the drag
        var mousePos = gamePosition([ev.pageX, ev.pageY]);
        gibbs.dragObj = objectForID( $(this).data('gibbsID') );
        gibbs.dragObj.startDrag(ev, mousePos);
        gibbs.lastMousePos = mousePos;
        return cancel(ev);
    });

    /*
     * Event: game .image mouseup
     * Checks and handles the end of an image drag
     */
    gibbs.game.on('mouseup', '.image', function(ev) {
        // release the drag, if necessary
        var mousePos = gamePosition([ev.pageX, ev.pageY]);
        if (gibbs.dragObj) {
            // check this position
            gibbs.dragObj.endDrag(ev, mousePos);
            gibbs.dragObj = null;
        }
        gibbs.lastMousePos = mousePos;
        cancel(ev);
    });

    gibbs.game.on('mousemove', function(ev) {
        if (gibbs.dragObj) {
            // move the object
            var mousePos = gamePosition([ev.pageX, ev.pageY]);
            var delta = [mousePos[0] - gibbs.lastMousePos[0], mousePos[1] - gibbs.lastMousePos[1]];
            gibbs.dragObj.move(delta);
        }
        gibbs.lastMousePos = mousePos;
    });

    // when the addGroup button is clicked, add a group
    $('#addGroup').on('click', function(ev) {
        var groupNum = gibbs.groups.length.toString();
        if (groupNum < GROUP_ROW * GROUP_COL) {
            var xNum = groupNum%4;
            var yNum = Math.floor(groupNum/4);
            console.log(groupNum);
            console.log(xNum);
            console.log(yNum);
            var newGroup = new Group([GROUP_MARGIN/2 + xNum*(GROUP_MARGIN + gibbs.groupSize[0]), GROUP_MARGIN/2 + yNum*(gibbs.groupSize[1] + GROUP_MARGIN)], gibbs.groupSize, "g" + groupNum);
            newGroup.addToScreen();
            gibbs.groups.push(newGroup);
        }
        else {
            warn('You cannot add any more groups');
        }
    });
    $('#warnButton').on('click', function(ev) {
        $('#warning').hide();
    });
});
