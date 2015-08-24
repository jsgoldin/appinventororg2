/**
 * Translate a title to a url safe title
 */
function wordToPrettyURL(word) {
    urlPrettyTitle = ""
    for (i = 0; i < word.length; i++) {
        if (word.charCodeAt(i) == 32) {
            urlPrettyTitle += '.'
        } else {
            urlPrettyTitle += word[i]
        }
    }
    return urlPrettyTitle;
}

/**
 * link to corresponding course page on course-box click
 */
$('.course-box').click(function () {
    window.location = document.URL + "/" + $(this).attr('identifier');
});

/**
 * link to corresponding module page on module-box click
 */
$('.module-box').click(
    function () {
        window.location = document.URL + "/"
            + wordToPrettyURL($(this).attr('module_title'));
    });

/**
 * link to corresponding content page on module-box click
 */
$('.content-box').click(
    function () {
        window.location = document.URL + "/"
            + wordToPrettyURL($(this).attr('content_title'));
    });

/**
 * More general hover link slide. Finds icon within class and slides it. Name a
 * class slide-left or slide-right for it to work.
 */
$('.slide-left').hover(function () {
    icon = $(this).find('.glyphicon');
    icon.stop();
    icon.animate({
        right: "4px"
    }, 150);
}, function () {
    icon = $(this).find('.glyphicon');
    icon.stop();
    icon.animate({
        right: "0px"
    }, 150);
});

$('.slide-right').hover(function () {
    icon = $(this).find('.glyphicon');
    icon.stop();
    icon.animate({
        left: "10px"
    }, 150);
}, function () {
    icon = $(this).find('.glyphicon');
    icon.stop();
    icon.animate({
        left: "0px"
    }, 150);
});

/**
 * Hover link arrow slide
 */
$('.vertical-side-bar-top-box-back').hover(function () {
    icon = $(this).find('.glyphicon');
    icon.stop();
    icon.animate({
        right: "4px"
    }, 150);
}, function () {
    icon = $(this).find('.glyphicon');
    icon.stop();
    icon.animate({
        right: "0px"
    }, 150);
});

/**
 * Hover link arrow slide
 */
$('.vertical-side-bar-top-bottom-next').hover(function () {
    icon = $(this).find('.glyphicon');
    icon.stop();
    icon.animate({
        left: "6px"
    }, 150);
}, function () {
    icon = $(this).find('.glyphicon');
    icon.stop();
    icon.animate({
        left: "0px"
    }, 150);
});

/**
 * Linkable vertical sidebar items
 */
$('.vertical-side-bar-item').click(function () {
    window.location = $(this).attr('content_ID');
})

/**
 * Linkable vertical sidebar items
 */
$('.vertical-side-bar-top-bottom-next').click(
    function () {
        url = String(document.URL).split('/');
        nextmod_id = $(this).attr('module_id');
        window.location = url[0] + '/' + url[1] + '/' + url[2] + '/'
            + url[3] + '/' + url[4] + '/' + nextmod_id;
});




function scrollToCurItemInSideBar() {
    var urlParts = window.location.href.split("/");
    var content_id = urlParts[urlParts.length - 1];

    // find vertical-side-bar-item with matching content_id
    // XXX: subtracted 100 to get correct value, might have to change if size of side bar items change
   var posElemInSideBar = $(".vertical-side-bar-item[content_ID='" + content_id + "']").position().top - 100;

   // calculate scrollTop
   var sideBarMiddleBox = $(".vertical-side-bar-middle-box");
   var scrollBottom = sideBarMiddleBox.height() + sideBarMiddleBox.scrollTop();

   var scrollDelta = posElemInSideBar - scrollBottom;

   // + 360 is to set the scroll so there are some items beneath current item
   sideBarMiddleBox.scrollTop(scrollDelta + 360);

}


$(document).ready(function() {

    scrollToCurItemInSideBar();

});

