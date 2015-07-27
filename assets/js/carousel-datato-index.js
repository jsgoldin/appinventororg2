
 var currentPage =0;
 $('#myCarousel').carousel({
         interval: false
     })
 $('#carousel-nav a').click(function(q){
    q.preventDefault();
    clickedPage = $(this).attr('data-to')-1;
    currentPage = clickedPage-1;
    $('#myCarousel').carousel(clickedPage);
    });
var pages = $("#carousel-nav a");
var pagesCount = pages.length;
$('#myCarousel').on('slide', function(evt) {
  $(pages).removeClass("active");
  currentPage++;
  currentPage=(currentPage%pagesCount);
  $(pages[currentPage]).addClass("active");
  });

