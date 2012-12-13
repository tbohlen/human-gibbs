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
gibbs.groups = [];
gibbs.images = [];
gibbs.objects = {};

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
    return gibbs.objects[index];
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
 * Function: randomizeList
 * Uses Knuth's algorithm to randomize a list
 */
function randomizeList(l) {
    var i;
    for (i = l.length-1; i > 0; i--) {
        randInd = Math.floor(Math.random() * i);
        switchElem = l[randInd];
        otherElem = l[i];
        l[randInd] = otherElem;
        l[i] = switchElem;
    }
}

/*
 * Function: loadImages
 * loads all images from server (or, as of now, from a given URL) and saves them
 * in the gibbs.images array
 */
function loadImages() {
    $.ajax({
        url: "/images",
        success: function(data) {
            var imageIDs = JSON.parse(data);
            for (i = 0; i < imageIDs.length; i++) {
                var id = imageIDs[i];
                var newImage = new Image("/images/" + id, gibbs.game, id);
                gibbs.objects[id] = newImage;
                gibbs.images.push(newImage);
            }
            // randomize
            randomizeList(gibbs.images);
        },
        async: false
    });
}

/*
 * Function: loadGroups
 * Creates the first group on screen
 */
function loadGroups() {
    var id = "g0";
    var newGroup = new Group([GROUP_MARGIN/2, GROUP_MARGIN/2], gibbs.groupSize, id);
    newGroup.addToScreen();
    gibbs.groups.push(newGroup);
    gibbs.objects[id] = newGroup;
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
    if (gibbs.nextImage >= gibbs.images.length) {
        $('#noMoreImages').show();
    }
    else {
        var image = gibbs.images[gibbs.nextImage];
        image.moveTo([-116, 30]);
        image.addToScreen();
        gibbs.nextImage++;
    }
}

/*
 * Function: sizeDocument
 * Sizes all resizable objects in the document
 */
function sizeDocument() {
    var pageHeight = document.height;
    var pageWidth = document.width;
    var i;
    //gibbs.game.width(pageWidth - (MARGIN * 2))
        //.height(pageHeight - TOP_MARGIN - BOTTOM_MARGIN);
    gameHeight = gibbs.game.height();
    gameWidth = gibbs.game.width();
    gibbs.gameHeight = gameHeight;
    gibbs.gameWidth = gameWidth;

    gibbs.groupSize = [(gameWidth/4) - GROUP_MARGIN, (gameHeight/2) - GROUP_MARGIN];

    for (i = 0; i < gibbs.groups.length; i++) {
        var xNum = i%4;
        var yNum = Math.floor(i/4);
        var group = gibbs.groups[i];
        group.moveTo([GROUP_MARGIN/2 + xNum*(GROUP_MARGIN + gibbs.groupSize[0]), GROUP_MARGIN/2 + yNum*(gibbs.groupSize[1] + GROUP_MARGIN)]);
        group.resize(gibbs.groupSize);
    }
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
    var x = -1;
    var y = -1;
    this.pos = [x, y];
    this.unstaged = false;
    this.group = 'g-1';

    // is the last known "ok" position of the object
    // generally this means it
    this.lastSolidPos = [x, y];
    // the pos if we were following the mouse perfectly. Saved to have nice
    // behavior when user tries to drag out of the game
    this.perfectPos = [x, y];

    this.object = $(document.createElement('img'));
    this.object.addClass('image');
    this.object.addClass('unselectable');
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
        this.cancelDrag(ev);
    }
    else {
        // if not unstaged, mark as unstaged and stage next
        if (!this.unstaged) {
            this.unstaged = true;
            showImage();
        }
        // modify the position so that it is inside the group
        var group = objectForID(groupID);
        this.perfectPos[0] = clamp(group.pos[0], group.pos[0] + group.size[0] - IMAGE_SIZE - 1, this.perfectPos[0]);
        this.perfectPos[1] = clamp(group.pos[1], group.pos[1] + group.size[1] - IMAGE_SIZE - 1, this.perfectPos[1]);
        this.moveTo(this.perfectPos);

        // record the data from the move
        var moveData = {
            id: parseInt(this.id),
            old_group: parseInt(this.group.substr(1)),
            new_group: parseInt(groupID.substr(1)),
            old_x: this.lastSolidPos[0],
            new_x: this.pos[0],
            old_y: this.lastSolidPos[1],
            new_y: this.pos[1],
            time_elapsed: 0
        };

        // post the move data in a form to the database
        var moveForm = new FormData();
        moveForm.append('move', JSON.stringify(moveData));
        
        $.ajax({
          url: "/move",
          data: moveForm,
          processData: false,
          contentType: false,
          type: 'POST'
        });

        // update variables that store previous state
        this.lastSolidPos = [this.pos[0], this.pos[1]];
        this.group = groupID
        this.object.removeClass('dragImage');
    }
};

/*
 * Method: cancelDrag
 * cancels a drag, dropping the image back at its lastSolidPos
 *
 * Parameters:
 * ev - the event that triggered the cancel
 *
 * Member Of: Image
 */
Image.prototype.cancelDrag = function(ev) {
    this.moveTo(this.lastSolidPos);
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

/*
 * Method: moveTo
 * Moves the group to a new position
 *
 * Parameters:
 * newPos - the new x and y coords
 *
 * Member Of: Group
 */
Group.prototype.moveTo = function(newPos) {
    this.perfectPos = [newPos[0], newPos[1]];

    this.pos[0] = clamp(0, gibbs.game.innerWidth() - IMAGE_SIZE - 1, this.perfectPos[0]);
    this.pos[1] = clamp(0, gibbs.game.innerHeight() - IMAGE_SIZE - 1, this.perfectPos[1]);

    this.object.css('left', this.pos[0]);
    this.object.css('top', this.pos[1])
};

/*
 * Method: resize
 * Resizes the group
 *
 * Parameters:
 * newSize - the new height and width of the group
 *
 * Member Of: Group
 */
Group.prototype.resize = function(newSize) {
    // TODO: if implementing manual resizing of groups include perfectSize and
    // clamping as in move and moveTo

    this.object.css('width', newSize[0]);
    this.object.css('height', newSize[1])
};

///////////////////////////////////////////////////////////////////////////////
/////////////////////////// Doc Ready Event Handler ///////////////////////////
///////////////////////////////////////////////////////////////////////////////

/*
 * Loads page on 'ready' event
 */
$(document).ready(function() {
    var game = $('#game');
    gibbs.game = game;
    sizeDocument();

    loadImages();
    loadGroups();
    showImage();

    // attach handlers
    
    $(document).on('mousedown', '.image', function(ev) {
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
    $(document).on('mouseup', '.image', function(ev) {
        // release the drag, if necessary
        var mousePos = gamePosition([ev.pageX, ev.pageY]);
        if (gibbs.dragObj) {
            // move the object
            var delta = [mousePos[0] - gibbs.lastMousePos[0], mousePos[1] - gibbs.lastMousePos[1]];
            gibbs.dragObj.move(delta);

            // end the drag and throw away the dragObj
            gibbs.dragObj.endDrag(ev, mousePos);
            gibbs.dragObj = null;
        }
        gibbs.lastMousePos = mousePos;
        return cancel(ev);
    });

    $(document).on('mousemove', function(ev) {
        if (gibbs.dragObj) {
            // move the object
            var mousePos = gamePosition([ev.pageX, ev.pageY]);
            var delta = [mousePos[0] - gibbs.lastMousePos[0], mousePos[1] - gibbs.lastMousePos[1]];
            gibbs.dragObj.move(delta);
        }
        gibbs.lastMousePos = mousePos;
        return cancel(ev);
    });

    // when the addGroup button is clicked, add a group
    $('#addGroup').on('click', function(ev) {
        var groupNum = gibbs.groups.length.toString();
        if (groupNum < GROUP_ROW * GROUP_COL) {
            var xNum = groupNum%4;
            var yNum = Math.floor(groupNum/4);
            var id = "GROUP" + groupNum
            var newGroup = new Group([GROUP_MARGIN/2 + xNum*(GROUP_MARGIN + gibbs.groupSize[0]), GROUP_MARGIN/2 + yNum*(gibbs.groupSize[1] + GROUP_MARGIN)], gibbs.groupSize, id);
            newGroup.addToScreen();
            gibbs.groups.push(newGroup);
            gibbs.objects[id] = newGroup;
        }
        else {
            warn('You cannot add any more groups');
        }
    });
    $('#warnButton').on('click', function(ev) {
        $('#warning').hide();
    });

    // mouseout on the document and game to avoid mouseup outside of window
    $(document).on('mouseleave', function(ev) {
        ev = ev ? ev : window.event;
        var nextElement = ev.relatedTarget;
        if (!nextElement || nextElement.nodeName == "HTML") {
            if (gibbs.dragObj) {
                // end the drag and throw away the dragObj to avoid issues with
                // mouseup outside
                gibbs.dragObj.cancelDrag(ev, gibbs.lastMousePos);
                gibbs.dragObj = null;
            }
        }
    });

    $(window).on('resize', function(ev) {
        sizeDocument();
        cancel(ev);
    });
});
