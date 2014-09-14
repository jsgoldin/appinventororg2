// load the IFrame Player API code asynchronously.

var tag = document.createElement('script');

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);


function getUTUBEID(url) {
	id_start = url.indexOf('/v/') + 3;
	url = url.slice(id_start);
	id_end = url.indexOf('&');
	if (id_end == -1) {
		// no query paramters
	} else {
		url = url.slice(0, id_end);
	}
	return url;
}

// load the videos
function onYouTubeIframeAPIReady() {
	// iterate through all the things django put in
	$('#carousel-wrapper').children().each(function() {
	
	
	
		videotarget = $(this).find('.carousel-step-video');

		desiredHeight = videotarget.width() * 0.56;

		videotarget.height(desiredHeight);

		video_id = getUTUBEID(videotarget.attr('data-utubeurl'));

		target_div = videotarget[0];
		player = new YT.Player(target_div, {
			height : '400px',
			width : 'auto',
			videoId : video_id,
			playerVars: {
            	'showinfo': 0
        	}
		});
	});

	$("#carousel-wrapper").owlCarousel({
	      slideSpeed : 300,
	      paginationSpeed : 400,
	      singleItem:true,
	      paginationNumbers: true,
	      lazyLoad : true
	  });
	
	// add custom navigation buttons
	
	$('.owl-pagination').prepend("<div id='carousel-nav-btn-left' class='carousel-nav-btn'><span class='glyphicon glyphicon-chevron-left'></span></div>");
	$('.owl-pagination').append("<div id='carousel-nav-btn-right' class='carousel-nav-btn'><span class='glyphicon glyphicon-chevron-right'></span></div>");
	return player;
}






var i = 1;
$(window).resize(function() {
	if(i % 2==0) {
		setTimeout(function() {
		
			if($('#carousel-nav-btn-left').length == 0) {
				$('.owl-pagination').prepend("<div id='carousel-nav-btn-left' class='carousel-nav-btn'><span class='glyphicon glyphicon-chevron-left'></span></div>");
			}

			if($('#carousel-nav-btn-right').length == 0) {
				$('.owl-pagination').append("<div id='carousel-nav-btn-right' class='carousel-nav-btn'><span class='glyphicon glyphicon-chevron-right'></span></div>");
     		}
     }, 700);
	}
	i++;
});



$(document).on("click","#carousel-nav-btn-left",function() {
	$(".owl-carousel").data('owlCarousel').prev();
});


$(document).on("click","#carousel-nav-btn-right",function() {
	$(".owl-carousel").data('owlCarousel').next();
});
