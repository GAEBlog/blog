  var AUTH={};AUTH.page="search";AUTH.user="{{authfor}}";AUTH.is=

   $.ajax({
      type: 'GET',
      url: "/api/blog/session",
      contentType: 'text/json',
      dataType: 'json',
      timeout: 30000,
      
      success: function(data){
        console.log(data)

        // signing and welcome buttons
        if (data.payload.authenticated) {
          $(".forauth").removeClass("hide");
          $(".forunauth").addClass("hide");
          $("#welcome_msg").text("Welcome " + data.payload.user_name);
          AUTH.user=data.payload.user_name;
          AUTH.is=true;
        }
        else {
          $(".forauth").addClass("hide");
          $(".forunauth").removeClass("hide");
          $("#welcome_msg").text("");
          AUTH.user="";
          AUTH.is=false;
        }
        
      },
      error: function(xhr, type){
        console.log(type);
        console.log(xhr);
      }
    });


      function sign_in() {
        
          $('#signin').modal();
      };

      $('#signin_button').click(sign_in);
      $('#register_button').click(sign_in);

      $("#sendtwsignin").click( function( event ) { signInClick('tw', event)});
      $("#sendfbsignin").click( function( event ) { signInClick('fb', event)});


      function signInClick( which, event ) {

        event.preventDefault();
        event.stopPropagation();
        

        if( which == 'tw') {
          location.href =  "/oauthinit?ch_pv=" + which;
        }
        else {

              FB.login(function(response) {
                  if (response.authResponse) {

                    FB.api('/me', function(meresponse) {
                      console.log('Good to see you, ' + meresponse.name + '.');
                        
                      payload = {
                        username: meresponse.name,
                        token: response.authResponse.accessToken,
                        secret: response.authResponse.signedRequest,
                        id: response.authResponse.userID,
                        page: location.href
                      };
                      

                      var dat = JSON.stringify(payload);

                      // send auth to the server
                      $.ajax({
                        type: 'POST',
                        url: "/api/blog/fb_session",
                        data: dat,
                        contentType: 'text/json',
                        dataType: 'json',
                        timeout: 30000,
                        
                        success: function(data) {
                          location.reload();
                        },
                        error: function(xhr, type){
                          console.log(type);
                          console.log(xhr);
                        }
                      }).done(function ( data ) {});

                    });

                  } else {
                      alert('not authenticated');
                  }
              });
        }
      }

