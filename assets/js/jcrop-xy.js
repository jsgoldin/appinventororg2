  var jcrop_api;
  var ifEnableCrop = 1;
  jQuery(function($){

    

    $('#targetxy').Jcrop({
      onChange:   showCoords,
      onSelect:   showCoords,
      onRelease:  clearCoords,
	 aspectRatio:1,
	 bgFade:     true,
	 bgOpacity: .2
      
    },function(){
      jcrop_api = this;
      

    });

    $('#coords').on('change','input',function(e){
      var x1 = $('#x1').val();
      var x2 = $('#x2').val();
      var y1 = $('#y1').val();
      var y2 = $('#y2').val();

	//var x_left = document.getElementById("x_left").value;
	//var x_right = document.getElementById("x_right ").value;
	//var y_top = document.getElementById("y_top").value;
	//var y_bottom = document.getElementById("y_bottom").value;
	//if(x1 < x_left){
	//return false;}
	//if(x2 > x_right){
	//return false;}
	//if(y1 < y_top){
	//return false;}
	//if(y2 > y_bottom){
	//return false;}



      jcrop_api.setSelect([x1,y1,x2,y2]);
    });

    
    jcrop_api.disable();

  });

  function crop_function()
  {
	if(ifEnableCrop == 1){
		ifEnableCrop = 0;
		enableCropPicture();
		document.getElementById('crop_function_button').value="Disable Cropping";
      }
      else
      {
		ifEnableCrop = 1;
		disableCropPicture();
		document.getElementById('crop_function_button').value="Enable Cropping";

      }
  }


  function disableCropPicture()
  {
    jcrop_api.disable();
  };
  function enableCropPicture()
  {
    jcrop_api.enable();

  };


  // Simple event handler, called from onChange and onSelect
  // event handlers, as per the Jcrop invocation above
  function showCoords(c)
  {
    $('#x1').val(c.x);
    $('#y1').val(c.y);
    $('#x2').val(c.x2);
    $('#y2').val(c.y2);
    $('#w').val(c.w);
    $('#h').val(c.h);

  };

  function clearCoords()
  {
    $('#coords input').val('');
  };







//checkinIfCroppingValid

function checkinIfCroppingValid()
  {
      var x1 = parseInt($('#x1').val());
      var x2 = parseInt($('#x2').val());
      var y1 = parseInt($('#y1').val());
      var y2 = parseInt($('#y2').val());

	var x_left = parseInt(document.getElementById("x_left").value);
	var x_right = parseInt(document.getElementById("x_right").value);
	var y_top = parseInt(document.getElementById("y_top").value);
	var y_bottom = parseInt(document.getElementById("y_bottom").value);



	if(x1 < x_left){
	alert("invalid x_left");
	return false;}
	if(x2 > x_right){
	alert("invalid x_right");
	return false;}
	if(y1 < y_top){
	alert("invalid y_top");
	return false;}
	if(y2 > y_bottom){
	alert("invalid y_bottom");
	return false;}

	

	return true;
  }










  // This is the preview function

  function previewImage(file)
        {
		

		 jcrop_api.setSelect([50,50,200,200]);

		 enableCropPicture();
		 /*
            var targetDiv = document.getElementById('targetxy');
		 var previewDiv = document.createElement('div');
		 previewDiv.setAttribute('id', 'preview');
		 
		 var imagePreview = document.createElement('img');
		 imagePreview.setAttribute('src', '/assets/img/avatar-default.gif');
 	      previewDiv.appendChild(imagePreview);

            targetDiv.appendChild(previewDiv);
		 */
            var MAXWIDTH  = 300;
            var MAXHEIGHT = 300;
            var div = document.getElementById('preview');
            if (file.files && file.files[0])
            {
                div.innerHTML = '<img id=imghead>';
                var img = document.getElementById('imghead');
                img.onload = function(){
                    var rect = clacImgZoomParam(MAXWIDTH, MAXHEIGHT, img.offsetWidth, img.offsetHeight);
                    img.width = rect.width;
                    img.height = rect.height;
                    img.style.marginLeft = rect.left+'px';
                    img.style.marginTop = rect.top+'px';

			    document.getElementById("x_left").value=rect.left;
			    document.getElementById("x_right").value=rect.left+rect.width;
			    document.getElementById("y_top").value=rect.top;
			    document.getElementById("y_bottom").value=rect.top+rect.height;

                }
			
                var reader = new FileReader();
                reader.onload = function(evt){img.src = evt.target.result;}
                reader.readAsDataURL(file.files[0]);
            }
            else
            {
                var sFilter='filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(sizingMethod=scale,src="';
                file.select();
                var src = document.selection.createRange().text;
                var objPreviewSizeFake = document.getElementById('preview_size_fake');
                objPreviewSizeFake.filters.item('DXImageTransform.Microsoft.AlphaImageLoader').src = src;
                div.innerHTML = '<img id=imghead>';

                var img = document.getElementById('imghead');
                img.filters.item('DXImageTransform.Microsoft.AlphaImageLoader').src = src;
                var rect = clacImgZoomParam(MAXWIDTH, MAXHEIGHT, objPreviewSizeFake.offsetWidth, objPreviewSizeFake.offsetHeight);
                status =('rect:'+rect.top+','+rect.left+','+rect.width+','+rect.height);
                div.innerHTML = "<div id=divhead style='width:"+rect.width+"px;height:"+rect.height+"px;margin-top:"+rect.top+"px;margin-left:"+rect.left+"px;"+sFilter+src+"\"'></div>";

			document.getElementById("x_left").value=rect.left;
			document.getElementById("x_right").value=rect.left+rect.width;
			document.getElementById("y_top").value=rect.top;
			document.getElementById("y_bottom").value=rect.top+rect.height;


            }
		 
		 
        }
        function clacImgZoomParam( maxWidth, maxHeight, width, height ){
            var param = {top:0, left:0, width:width, height:height};
            if( width>maxWidth || height>maxHeight )
            {
                rateWidth = width / maxWidth;
                rateHeight = height / maxHeight;

                if( rateWidth > rateHeight )
                {
                    param.width =  maxWidth;
                    param.height = Math.round(height / rateWidth);
                }else
                {
                    param.width = Math.round(width / rateHeight);
                    param.height = maxHeight;
                }
            }

            param.left = Math.round((maxWidth - param.width) / 2);
            param.top = Math.round((maxHeight - param.height) / 2);
            return param;
        }




function showFileSize() {
    var input, file;

    // (Can't use `typeof FileReader === "function"` because apparently
    // it comes back as "object" on some browsers. So just see if it's there
    // at all.)
    if (!window.FileReader) {
	  alert("The file API isn't supported on this browser yet.");
        return false;
    }

    input = document.getElementById('picturefile');
    if (!input) {
	   alert("Um, couldn't find the fileinput element.");
	   return false;

    }
    else if (!input.files) {
	  alert("This browser doesn't seem to support the `files` property of file inputs.");
	  return false;

    }
    //else if (!input.files[0]) {
    //    alert("Please select a file before clicking 'Upload'");
    //	  return false;

    //}
    else {
        file = input.files[0];
	   if(file.size > 1024000){
        alert("File " + file.name + " is " + file.size/1024 + " kb; maxium is 1000kb");
	   return false;
	   }else{
	   return true;
	   }
    }
}











  