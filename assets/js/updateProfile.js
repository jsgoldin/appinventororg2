$('input:radio[name="educatorRadio"]').change(function() {
	if ($(this).val() == 'Yes') {
		$("#educatorCollapsable").collapse('show')
	} else if ($(this).val() == 'No') {
		$("#educatorCollapsable").collapse('hide')
	}
});


$(".uploadPhotoBoxWrapper").hover(function() {
	$(".uploadPhotoBox").addClass("photoHover");
}, function() {
	$(".uploadPhotoBox").removeClass("photoHover");
});

$(".uploadPhotoBoxWrapper").click(function() {
	$("#pictureFile").click();
});

function submitPhoto() {
	$("#photoForm").submit();
}

function updateProfile() {
	// get data from the registration form
	var firstName = $("#firstName").val();
	var lastName = $("#lastName").val();
	var displayName = $("#displayName").val();
	var location = $("#location").val();
	var isEducator = false;
	var organization = "";
	var educationLevel = "";
	var website = "";
	console.log(pictureFile);
	if ($("#isEducatorRadio").is(':checked')) {
		isEducator = true;
		organization = $("#organization").val();
		educationLevel = $("#educationLevel").val();
		website = $("#website").val();
	}



	$.post("/updateAccount", {
		sfirstName : firstName,
		slastName : lastName,
		sdisplayName : displayName,
		sisEducator : isEducator,
		sorganization : organization,
		seducationLevel : educationLevel,
		swebsite : website,
		slocation : location,
		sisEducator : isEducator,
	}).done(function(data) {
		// the alert here is awful, but we need it because the
		// datastore for accounts does not use an ancestor group
		// and needs a delay to take effect...
		alert("Changes Saved!");
		window.location = "/profile"
	});
}
