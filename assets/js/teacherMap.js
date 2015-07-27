var curInfoWindow = null;

function initialize() {
	var mapOptions = {
		center : {
			lat : 20,
			lng : 0
		},
		zoom : 2,
	    scrollwheel: false,
	};
	
	
		
	map = new google.maps.Map(document.getElementById('googleMap'),
			mapOptions);
	
	
	$.get("/getEducatorsInfo", function(data, status){
		teachers = JSON.parse(data).teachers;
		for(var i = 0; i < teachers.length; i++) {
			if(teachers[i].coord.lat !=null && teachers[i].coord.long != null) {
				
				var currentTeacher = teachers[i];
				console.log(currentTeacher);
				
				var myLatlng = new google.maps.LatLng(currentTeacher.coord.lat, currentTeacher.coord.long);
				var image = "/assets/img/androidMapMarker.png"

				var contentString = "<h5>" + currentTeacher.name + "</h5>";
				if(currentTeacher.educationLevel != "") {
					contentString += "<p>" + currentTeacher.educationLevel + "</p>";
				}
				
				if(currentTeacher.organization != "") {
					contentString += "<p>" + currentTeacher.organization + "</p>";
				}

				
				var myInfowindow = new google.maps.InfoWindow({
					content:  contentString,
				});
				
				var marker = new google.maps.Marker({
				    position: myLatlng,
				    title: currentTeacher.name,
				    infowindow: myInfowindow
				});
				
				marker.setMap(map);
				
				google.maps.event.addListener(marker, 'click', function() {
					 if (curInfoWindow != null) {
						 curInfoWindow.close();
						 curInfoWindow = this.infowindow;
					 } else {
						 curInfoWindow = this.infowindow;
					 }
					
					this.infowindow.open(map, this);
				});
			}
		}
		
		$.get("/getEducatorsTiles", function(data, status) {
			$("article").append(data);
		});		
		
		
		
    });
	
	
}


google.maps.event.addDomListener(window, 'load', initialize);