$(function() {
    
    "use strict";
    
    //===== Prealoder
    
    $(window).on('load', function(event) {
        $('.preloader').delay(500).fadeOut(500);
    });
    
    
    //===== Sticky
    
    $(window).on('scroll', function(event) {    
        var scroll = $(window).scrollTop();
        if (scroll < 10) {
            $(".header-navbar").removeClass("sticky");
        } else{
            $(".header-navbar").addClass("sticky");
        }
    });
    
    
    //===== Mobile Menu
    
    $(".navbar-toggler").on('click', function() {
        $(this).toggleClass("active");
    });
    
    var subMenu = $('.sub-menu-bar .navbar-nav .sub-menu');
    
    if(subMenu.length) {
        subMenu.parent('li').children('a').append(function () {
            return '<button class="sub-nav-toggler"> <i class="fa fa-chevron-down"></i> </button>';
        });
        
        var subMenuToggler = $('.sub-menu-bar .navbar-nav .sub-nav-toggler');
        
        subMenuToggler.on('click', function() {
            $(this).parent().parent().children('.sub-menu').slideToggle();
            return false
        });
        
    }
    
    
    //===== Counter
    
    $('.counter').counterUp({
        delay: 10,
        time: 2000,
    });
    
    
    
    //===== Back to top
    
    // Show or hide the sticky footer button
    $(window).on('scroll', function(event) {
        if($(this).scrollTop() > 600){
            $('.back-to-top').fadeIn(200)
        } else{
            $('.back-to-top').fadeOut(200)
        }
    });
    
    
    //Animate the scroll to Top
    $('.back-to-top').on('click', function(event) {
        event.preventDefault();
        
        $('html, body').animate({
            scrollTop: 0,
        }, 1500);
    });
    
    
    
    //=====  Nice Select
    
    $('select').niceSelect();
    
    
    
    //===== Slick Companies
    
    $('.companies_active').slick({
        dots: true,
        infinite: false,
        arrows: false,
        prevArrow: false,
        speed: 800,
        slidesToShow: 4,
        responsive: [
            {
              breakpoint: 1200,
              settings: {
                slidesToShow: 4,
              }
            },
            {
              breakpoint: 992,
              settings: {
                slidesToShow: 3,
              }
            },
            {
              breakpoint: 768,
              settings: {
                slidesToShow: 2,
              }
            },
            {
              breakpoint: 576,
              settings: {
                slidesToShow: 1,
              }
            }
        ]
    });
    
    
    
    //===== slick testimonials
    
    $('.testimonials_active').slick({
        dots: true,
        infinite: true,
        arrows: false,
        speed: 800,
        slidesToShow: 1,
    });
    
    
    
    //===== Sidebar
    
    
    $('#dismiss, .overlay').on('click', function () {
        $('#sidebar').removeClass('active');
        $('.overlay').removeClass('active');
    });
    
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').addClass('active');
        $('.overlay').addClass('active');
    });
    
    
    //===== Summer Note
    
    $('#summernote').summernote({
        height: 200,                 // set editor height
    });
    
    
    //===== Date Picker
    
    $('#datepicker').datepicker({
        uiLibrary: 'bootstrap4',
        format: 'yyyy-dd-mm',
        showRightIcon: false,
        iconsLibrary: 'fontawesome',
        icons: {
             rightIcon: '<span class="glyphicon glyphicon-chevron-down"></span>',
         }
    });
    
    
    
    
});