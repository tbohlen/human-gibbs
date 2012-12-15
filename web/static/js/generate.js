$(document).ready(function() {
    $("#generate").on('click', function() {
        $.ajax({
            url: "/gen",
            success: function(data) {
                $("#result").text(data)
            },
            type: 'POST'
        });
    });
});
