/**
 * The following is used on the Admin Modules page!
 * 
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
document.getElementById('edit_icon').addEventListener('change', handleFileSelect, false);
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


$('#updateModulebtn').click(function() {
    // gather the data from the editModal
    title = $('#edit_module_title').val();
    description = $('#edit_module_description').val();
    icon = $('#edit_icon_img').attr('src');
    identifier = $('#edit_module_identifier').val()
    course_id = $('.subject-box-top-half-inner').attr('course_id');
    module_id = $('#editModal').attr('module_id');
    
    // post it to the server and refresh the page
    if (title == "") {
        alert("title cannot be empty!")
    } else {
        $.post("/admin/course_system/update/Module", {
            s_module_id: module_id,
            s_course_id: course_id,
            s_title: title,
            s_description: description,
            s_icon: icon,
            s_identifier: identifier
        }, function(data, status) {
            location.reload(true);
        });
    }
});


/* edit button */
$(document).on('click', '#editmodulebtn', function() {
    // get current attributes of content
    content_root = $(this).parent().parent();
    title = content_root.find('h1');
    description = content_root.find('p');
    // set modal form inputs to current content values
    $('#edit_module_title').val(title.text());
    $('#edit_module_description').val(description.text());
    $('#edit_icon_img').attr('src', content_root.find('img').attr('src'));
    $('#edit_module_identifier').val(content_root.attr('identifier'));
    // how should i set the file chooser?
    // have actual button offscreen!
    // set some sneaky modal attributes for later XP
    $('#editModal').attr('module_id', content_root.attr('keyid'));
});



$("#createModulebtn").click(function(event) {
	
    new_title = $("#ModuleTitle").val();
    new_description = $("#ModuleDescription").val();
    file = $('#ModuleIcon').get(0).files[0];
    identifier = $('#ModuleIdentifier').val();
    
    var reader = new FileReader();
    var dataURL = null;
    
    

    // Closure to capture the file information.
    reader.onload = (function(theFile) {
        return function(e) {
            dataURL = e.target.result;
            $.post("/admin/course_system/create/Module", {
                title: new_title,
                course_id: $('.subject-box-top-half-inner').attr('course_id'),
                description: new_description,
                s_identifier : identifier,
                icon: dataURL,
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
$(document).ready(function() {
    var insideNoClick = false;
    /*
	 * Clickable item boxes that take you to corresponding content page
	 */
    $(document).on('click', '.module-edit-box', function() {
        if (insideNoClick == true) {
            // alert("NO LINK!");
        } else {
            window.location = document.URL + "/" + $(this).attr('identifier');
        }
    });
    // XXX DONE
    /* Highlight item boxes on hover */
    $(".module-edit-box").mouseover(function() {
        $(this).addClass('hover');
        $(this).find(".item-box-btns").removeClass('hidden');
    });
    $(".module-edit-box").mouseout(function() {
        $(this).removeClass('hover');
        $(this).find(".item-box-btns").addClass('hidden');
    });
    // / XXX DONE
    /* Move module button */
    $(document).on('mouseover', '#movemodulebtn', function() {
        $(this).parent().parent().attr('id', '');
    });
    $(document).on('mouseout', '#movemodulebtn', function() {
        $(this).parent().parent().attr('id', 'noDrag');
    });
    // TODO: IMPLEMENT
    /* Delete module button */
    $(document).on('click', '#deletemodulebtn', function() {
        s_module_id = $(this).parent().parent().attr('keyid');
        s_course_id = $('.subject-box-top-half-inner').attr('course_id');
        course_Title = $('.subject-box-top-half-inner').attr('course_title');
        $.post("/admin/course_system/delete/Module", {
            module_id: s_module_id,
            course_id: s_course_id
        }, function(data, status) {
            location.reload(true)
        });
    });
    /*
	 * Prevent certain items from linking to content page on click
	 */
    $(document).on('mouseover', '.noclick', function() {
        insideNoClick = true;
    });
    $(document).on('mouseout', '.noclick', function() {
        insideNoClick = false;
    });
   
    /* Allow drag and drop */
    $(function() {
        $("#sortable").sortable({
            cancel: "#noDrag",
            stop: function(event, ui) {
                saveOrder();
            }
        });
    });

    function saveOrder() {
        var index = -1;
        var resultArray = "";
        $("#sortable").children().each(function() {
            resultArray += ++index + ",";
            resultArray += $(this).attr('keyid') + ",";
        });
        $.post("/admin/course_system/reorder/Module", {
            s_array: resultArray,
            course_id: $(".subject-box-top-half-inner").attr("course_id")
        }, function(data, status) {
            location.reload(true);
        });
    }
});