//only allow one video per step, otherwise, dynamic player ID will duplicate



// 2. This code loads the IFrame Player API code asynchronously.
      var tag = document.createElement('script');

      // This is a protocol-relative URL as described here:
      //     http://paulirish.com/2010/the-protocol-relative-url/
      // If you're testing a local page accessed via a file:/// URL, please set tag.src to
      //     "https://www.youtube.com/iframe_api" instead.
      tag.src = "https://www.youtube.com/iframe_api";
      var firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

      // 3. This function creates an <iframe> (and YouTube player)
      //    after the API code downloads.

      var videoIdList = new Array();
 
	 var videoNameList = new Array();
 

      var videoPlayerList = new Array();


      function onYouTubeIframeAPIReady() {

	  for (var i = 0; i < videoIdList.length; i++) {
    	     videoPlayerList[i]=new YT.Player(videoNameList[i], {
          		//height: '700',
          		//width: '1230',
          		videoId: videoIdList[i]
          	      
           });
	  }

        


      }

  	function addVideo(link, name){
		id = link.substr(link.length-11,link.length);
		videoIdList.push(id);
		videoNameList.push(name);
  	}

	
      
      function stopVideo() {
		for (var i = 0; i < videoIdList.length; i++) {
			videoPlayerList[i].stopVideo();
		}


      }