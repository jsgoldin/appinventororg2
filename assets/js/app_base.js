/* This file contains functionality for the app tutorial videos, mainly the carousel. */


// load the IFrame Player API code
var tag = document.createElement('script');
tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

var currentSlide = 0;


// data object for manipulating owl carousel
var owl_carousel_data;


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

var videoArray = []; /* maintains a reference to all videos on the page. */

/**
 * Creates IFrame for each video in the carousel. This method is called by the
 * YouTube IFrame player API once the API is loaded successfully.
 */
function onYouTubeIframeAPIReady() {
	// iterate through all the things django put in

	// iterate through each carousel step
	$('#carousel-wrapper').children().each(
			function() {
				videotarget = $(this).find('.carousel-step-video');
				desiredHeight = videotarget.width() * 0.56;
				videotarget.height(desiredHeight);
				video_id = getUTUBEID(videotarget.attr('data-utubeurl'));
				console.log("path: " + videotarget.attr('data-utubeurl')
						+ " video_id: " + video_id);
				target_div = videotarget[0];
				player = new YT.Player(target_div, {
					height : '400px',
					width : 'auto',
					videoId : video_id,
					playerVars : {
						'showinfo' : 0
					},
					events : {
						'onStateChange' : onPlayerStateChange
					}
				});

				// save all videos on page to videoArray for reference later.
				videoArray.push(player);
			});

	// generate the Owl Carousel
	var m_owl_carousel = $("#carousel-wrapper").owlCarousel({
		slideSpeed : 300,
		paginationSpeed : 400,
		singleItem : true,
		paginationNumbers : true,
		lazyLoad : true,
		navigation : false,
		afterAction : updatecurrentSlide,
		afterMove: moveHandler,
	});

	owl_carousel_data = m_owl_carousel.data('owlCarousel');



	var leftButtonHTML = "<div id=\"leftNav\" class=\"owl-custom-nav-btn\"><span class=\"glyphicon glyphicon-chevron-left\""
			+ "aria-hidden=\"true\"></span></div>";
	var rightButtonHTML = "<div id=\"rightNav\" class=\"owl-custom-nav-btn\"><span class=\"glyphicon glyphicon-chevron-right\""
			+ "aria-hidden=\"true\"></span></div>";

	// insert custom side nav buttons
	$(".owl-pagination").prepend(leftButtonHTML);
	$(".owl-pagination").append(rightButtonHTML);

	// attach them to owl navF
	$("#leftNav").click(function() {
		owl_carousel_data.prev();
	});

	$("#rightNav").click(function() {
		owl_carousel_data.next();
	});

	// attach end overlay buttons
	$(".app-btn-next").click(function() {
		owl_carousel_data.next();
	});

	$(".app-btn-rewatch").click(
			function() {

				// get player object of current slide
				var currentVideoPlayer = videoArray[$(".owl-carousel").data(
						'owlCarousel').currentItem];

				// hide the overlay
				currentSlide.find(".carousel-step-end-overlay").hide();

				// play the video
				currentVideoPlayer.playVideo();
			});

	function updatecurrentSlide() {
		var targetItemIndex = this.owl.currentItem + 1;
		currentSlide = $(".owl-item:nth-child(" + targetItemIndex + ")");
	}

	function onPlayerStateChange(event) {

		if (event.data == YT.PlayerState.ENDED) {
			currentSlide.find(".carousel-step-end-overlay").show();
		} else if (event.data == YT.PlayerState.PLAYING) {
			currentSlide.find(".carousel-step-info").hide();
		} else if (event.data == YT.PlayerState.PAUSED) {
			currentSlide.find(".carousel-step-info").show();
		}
	}

	function stopAllVideos() {
		for (var i = 0; i < videoArray.length; i++) {
			videoArray[i].pauseVideo();
		}
	}

	function updateTableOfContents() {
		$(".video-steps-box > div").removeClass("selected");
		$(".video-steps-box > div:nth-child(" + (owl_carousel_data.currentItem + 1 ) + ")").addClass("selected");
	}

	$(".video-steps-box > div").click(function() {
		var newIndex = $(this).index();
		owl_carousel_data.goTo(newIndex);
undefined
	});



	function moveHandler() {
		stopAllVideos();
		updateTableOfContents();

	}

}