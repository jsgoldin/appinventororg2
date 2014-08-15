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
      var player1;
      var player2;
	 var player3;

	
      YT.embed_template = "\u003ciframe width=\"425\" height=\"344\" src=\"\" frameborder=\"0\" allowfullscreen\u003e\u003c\/iframe\u003e";

      function onYouTubeIframeAPIReady() {
        player1 = new YT.Player('youtube_player1', {
          height: '360',
          width: '515',

	     videoId: 'HbntNGGXamw',

          
          
        });
		  
	   player2 = new YT.Player('youtube_player2', {
          height: '360',
          width: '515',
	     videoId: 'sGiaXOKqeKg',
          events: {
            
           
          }
        });

	   player3 = new YT.Player('youtube_player3', {
          height: '360',
          width: '515',
          videoId: 'cWzrhYwn0xk',
          events: {
            
           
          }
        });

	  player4 = new YT.Player('youtube_player4', {
          height: '360',
          width: '515',
          videoId: 'E9Zm56Od1pw',
          events: {
            
           
          }
        });

	 player5 = new YT.Player('youtube_player5', {
          height: '360',
          width: '515',
          videoId: 'qOE0avT5v68',
          events: {
            
           
          }
        });

	 player6 = new YT.Player('youtube_player6', {
          height: '360',
          width: '515',
          videoId: '8wsGnG_yNrQ',
          events: {
            
           
          }
        });

	  



      }

      


      // 5. The API calls this function when the player's state changes.
      //    The function indicates that when playing a video (state=1),
      //    the player should play for six seconds and then stop.
      var done = false;
      
      function stopVideo() {
        player1.stopVideo();
	  player2.stopVideo();
       player3.stopVideo();
       player4.stopVideo();
       player5.stopVideo();
       player6.stopVideo();

      }
