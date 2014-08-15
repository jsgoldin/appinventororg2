var geocoder, map, marker;
  var defaultLatLng = new google.maps.LatLng(30,0);
 
  function initialize() {
    geocoder = new google.maps.Geocoder();
  }
 
  function validate() {

    clearResults();
    var address = document.getElementById('address').value;
    geocoder.geocode({'address': address }, function(results, status) {
      switch(status) {
        case google.maps.GeocoderStatus.OK:
          


		var i = 0;
		for(i = 0; i < results.length; i++){
			if(results[i]){
				var id = 'result'+i;
				document.getElementById(id).innerHTML = results[i].formatted_address;
				document.getElementById('result' + i).style.display='';

				
			}else{
				break;
			}

		}

          break;
        case google.maps.GeocoderStatus.ZERO_RESULTS:
          
	     document.getElementById('noresultsfound').innerHTML = 'sorry, please provide more location information';
          break;
        default:
	     document.getElementById('noresultsfound').innerHTML = 'sorry, please provide more location information';

      }
    });
  }
 
  function clearResults() {

    document.getElementById('result0').innerHTML = '';
    document.getElementById('result1').innerHTML = '';
    document.getElementById('result2').innerHTML = '';
    document.getElementById('noresultsfound').innerHTML = '';
    
    document.getElementById('result0').style.display='none';
    document.getElementById('result1').style.display='none';
    document.getElementById('result2').style.display='none';
    




  }

  function replaceAddress(id){
    document.getElementById('address_valid').value = document.getElementById(id).innerHTML;
    
  }