// load the IFrame Player API code asynchronously.
var tag = document.createElement('script');
tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

/**
 * Parses and returns the video id from a youtube video url.
 */
function getUTUBEID(url) {
	id_start = url.indexOf('/v') + 3;
	url = url.slice(id_start);
	id_end = url.indexOf('&');
	if (id_end == -1) {
		// no query paramters
	} else {
		url = url.slice(0, id_end);
	}
	return url;
}


var videoArray = [];	/* maintains a reference to all videos on the page. */

/**
 * Load the videos
 */
function onYouTubeIframeAPIReady() {
	// iterate through all the things django put in
	$('#carousel-wrapper').children().each(function() {
		videotarget = $(this).find('.carousel-step-video');
		desiredHeight = videotarget.width() * 0.56;
		videotarget.height(desiredHeight);
		video_id = getUTUBEID(videotarget.attr('data-utubeurl'));
		console.log("path: " + videotarget.attr('data-utubeurl') + " video_id: " + video_id);
		target_div = videotarget[0];
		player = new YT.Player(target_div, {
			height : '400px',
			width : 'auto',
			videoId : video_id,
			playerVars : {
				'showinfo' : 0
			}
		});
		
		videoArray.push(player);
		
	});

	$("#carousel-wrapper").owlCarousel({
		slideSpeed : 300,
		paginationSpeed : 400,
		singleItem : true,
		paginationNumbers : true,
		lazyLoad : true,
		afterAction : stopAllVideos,
		navigation : true,
		navigationText: [
		                 "<span class=\"glyphicon glyphicon-chevron-left\" aria-hidden=\"true\"></span>",
		                 "<span class=\"glyphicon glyphicon-menu-right\" aria-hidden=\"true\"></span>",
		                 ],
	});
	
	
	function stopAllVideos() {
		for (var i = 0; i < videoArray.length; i++) {
		    videoArray[i].pauseVideo();
		}
	}
	
	
	
	/*
	// add custom navigation buttons
	$('.owl-pagination').prepend(
		"<div id='carousel-nav-btn-left' class='carousel-nav-btn'>" +
		"	<span class='glyphicon glyphicon-chevron-left'>" +
		"	</span>" +
		"</div>");
	$('.owl-pagination').append(
		"<div id='carousel-nav-btn-right' class='carousel-nav-btn'>" +
		"	<span class='glyphicon glyphicon-chevron-right'>" +
		"	</span>" +
		"</div>");
	return player;
	*/
	
}



/*
// TODO: FIX!
$(document).on("click", "#carousel-nav-btn-left", function() {
	// $(".owl-carousel").data('owlCarousel').prev();	
});

$(document).on("click", "#carousel-nav-btn-right", function() {
	// var owl = $('.owl-carousel');
	// owl.trigger('next.owl.carousel');
	// $(".owl-carousel").data('owlCarousel').next();
});
*/