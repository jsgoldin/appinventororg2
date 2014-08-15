/*
 *	The following is used on the admin courses editor page!
 */

function handleFileSelect(evt) {
	files = evt.target.files;
	if (files.length == 0) {
		// alert('no file chose')
	} else {
		f = files[0];
		reader = new FileReader();
		reader.onload = (function(theFile) {
			return function(e) {
				// Render thumbnail
				$('#edit_icon_img').attr('src', e.target.result);
			};
		})(f);
		reader.readAsDataURL(f);
	}
}
/* event listener for icon file input */
document.getElementById('edit_icon').addEventListener('change',
		handleFileSelect, false);
/* Change module icon click */
$('#edit_icon_btn').click(function() {
	$('#edit_icon').trigger('click');
});
/* Highlight on mouseover of change icon button */
$('#edit_icon_btn').mouseover(function() {
	$('#edit_icon_btn_text').show();
	$('#edit_icon_img').addClass('hover-opacify');
});

$('#edit_icon_btn').mouseout(function() {
	$('#edit_icon_btn_text').hide();
	$('#edit_icon_img').removeClass('hover-opacify');
});

/* Update Course */
$('#updateCourse').click(function() {
	// gather the data from the editModal
	title = $('#edit_course_title').val();
	
	description = $('#edit_course_description').val();
	icon = $('#edit_icon_img').attr('src');
	course_id = $('#editModal').attr('course_id');
	identifier = $('#edit_course_identifier').val();
	
	// post it to the server and refresh the page
	if (title == "") {
		alert("title cannot be empty!")
	} else {
		$.post("/admin/course_system/update/Course", {
			s_course_id : course_id,
			s_title : title,
			s_description : description,
			s_icon : icon,
			s_identifier : identifier
		}, function(data, status) {
			location.reload(true);
		});
	}
});

/* edit button */
$(document).on('click', '#editcoursebtn', function() {
	// get current attributes of course
	course_root = $(this).parent().parent();

	title = course_root.find('h1');
	description = course_root.find('p');

	// set modal form inputs to current content values
	$('#edit_course_title').val(title.text());
	$('#edit_course_description').val(description.text());
	$('#edit_icon_img').attr('src', course_root.find('img').attr('src'));
	// set some sneaky modal attributes for later XP
	$('#editModal').attr('course_id', course_root.attr('keyid'));
	$('#edit_course_identifier').val(course_root.attr('identifier'));
	
});

$(document).ready(function() {
	// if insideNoClick is true the click will not link
	var insideNoClick = false;

	// XXX DONE
	/*
	 * Clickable item boxes that take you to corresponding content page
	 */
	$(document).on('click', '.course-box', function() {
		if (insideNoClick == true) {
			// alert("NO LINK!");
		} else {
			window.location = "courses/" + $(this).attr('identifier');
		}
	});

	
	/*
	 * Handles the creation of new courses, The data from the course creation
	 * form is retrieved and sent to the server for storage in the datastore.
	 */
	$("#createCoursebtn").click(function(event) {		
		
		new_title = $("#CourseTitle").val();

		new_description = $("#CourseDescription").val();
		file = $('#CourseIcon').get(0).files[0];

		s_last_index = $('#sortable').children().last().attr('index');
		
		
		new_identifier = $("#CourseIdentifier").val();
		
		// check if s_last_index is undefined
		if(! s_last_index) {
			s_last_index = 1;
		}
		
		var reader = new FileReader();
		var dataURL = null;

		
		// Closure to capture the file information.
		reader.onload = (function(theFile) {
			return function(e) {
				dataURL = e.target.result;
				$.post("/admin/course_system/create/Course", {
					title : new_title,
					description : new_description,
					icon : dataURL,
					last_index : s_last_index,
					s_identifier : new_identifier
				}, function(data, status) {
					location.reload(true);
				});
			};
		})(file);	

		validated = true;
		errorString = "Missing required fields\n\n";

		if (file == undefined) {
			errorString += "\tYou must select an icon!\n";
			validated = false;
		}

		if (new_title == "") {
			errorString += "\tYou must enter a title!\n";
			validated = false;
		}

		if (validated) {
			reader.readAsDataURL(file);
		} else {
			alert(errorString)
		}
	});

	// XXX DONE
	/* Highlight item boxes on hover */
	$(".course-box").mouseover(function() {
		$(this).addClass('hover');
		$(this).find(".item-box-btns").removeClass('hidden');
	});

	// XXX DONE
	$(".course-box").mouseout(function() {
		$(this).removeClass('hover');
		$(this).find(".item-box-btns").addClass('hidden');
	});

	// XXX DONE
	/* Move module button */
	$(document).on('mouseover', '#movecoursebtn', function() {
		$(this).parent().parent().attr('id', '');
	});

	// XXX DONE
	$(document).on('mouseout', '#movecoursebtn', function() {
		$(this).parent().parent().attr('id', 'noDrag');
	});

	// XXX DONE
	/* Delete Course button */
	$(document).on('click', '#deletecoursebtn', function() {
		s_keyid = $(this).parent().parent().attr('keyid');

		$.post("/admin/course_system/delete/Course", {
			course_id : s_keyid
		}, function(data, status) {
			location.reload(true);
		});

	});

	// XXX DONE
	/* Prevent certain items from linking to content page on click */
	$(document).on('mouseover', '.noclick', function() {
		insideNoClick = true;
	});

	// XXX DONE
	$(document).on('mouseout', '.noclick', function() {
		insideNoClick = false;
	});
	
	// XXX DONE
	/* Allow drag and drop */
	$(function() {
		$("#sortable").sortable({
			cancel : "#noDrag",
			stop : function(event, ui) {
				saveOrder()
			}
		});
	});

	// XXX DONE
	function saveOrder() {
		var index = -1;
		var resultArray = "";
		$("#sortable").children().each(function() {
			resultArray += ++index + ",";
			resultArray += $(this).attr('keyid') + ",";
		});

		$.post("/admin/course_system/reorder/Course", {
			s_resultArray : resultArray,
		}, function(data, status) {
			location.reload(true);
		});
	}


});
