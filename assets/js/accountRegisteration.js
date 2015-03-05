$('input:radio[name="educatorRadio"]').change(function() {
	if ($(this).val() == 'Yes') {
		$("#educatorCollapsable").collapse('show')
	} else if ($(this).val() == 'No') {
		$("#educatorCollapsable").collapse('hide')
	}
});

function submitForm() {

	// get data from the registration form
	var firstName = $("#firstName").val();
	var lastName = $("#lastName").val();
	var displayName = $("#displayName").val();
	var isEducator = false;
	var organization = "";
	var educationLevel = "";
	var website = "";
	var location = "";
	if ($("#isEducatorRadio").is(':checked')) {
		isEducator = true;
		organization = $("#organization").val();
		educationLevel = $("#educationLevel").val();
		website = $("#website").val();
		location = $("#location").val();
	}

	$.post("/registerAccount", {
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
		window.location = "/";		
	});
}