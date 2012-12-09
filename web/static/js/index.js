var MARGIN = 100;
var TOP_MARGIN = 50;
var BOTTOM_MARGIN = 50;
$(document).ready(function() {
    console.log('Loaded');
    var pageHeight = document.height;
    var pageWidth = document.width;
    var game = $('#game');
    game.width(pageWidth - (MARGIN * 2))
        .height(pageHeight - TOP_MARGIN - BOTTOM_MARGIN);
});
