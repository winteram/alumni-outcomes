function initAlumni()
{
  $.post('/extras',{'func':'init'},
    function(data)
    {
      if (data.hasOwnProperty('ecode')) { 
        switch(data.ecode)
        {
          case 300:
            if(data.n_templates == 0)
            {
              $("#new-or-old input:radio").attr('disabled',true);
              $('#create-button').click(verifyTemplate());
            }
            else
            {
              $("#new-or-old input:radio").change(function(){
                // Show new template or loading templates
                if($('input[name=noo-radio]:checked', '#new-or-old').val() == 'new')
                {
                  $('#new-template').show();
                  $('load-template').hide();
                } else {
                  $('load-template').show();
                  $('#new-template').hide();
                }
              });
              // Add select option for available templates
              load_template_str = '<select>';
              for (var i = data.templates.length - 1; i >= 0; i--) {
                load_template_str += "<option value='" + data.templates[i].short + "'>";
                load_template_str += data.templates[i].name + "</option>";
              };
              load_template_str += '</select>';
              // Add button to begin
              load_template_str += '<input type="button" name="crawl" value="Begin" onclick="beginCrawl()" />';
              $('#load-template').html(load_template_str);
            }
            break;
          default:
            console.log('Error in progress bar: ' + data.ecode);
        }
      } else {
        console.log('Error in init: ' + data);
      }
    }, "json");
}

function verifyTemplate()
{
  console.log('Would verify template here');
}

function makeProgress()
{
  var progressbar = $( "#progressbar" ), progressLabel = $( ".progress-label" );

  progressbar.progressbar({
    value: false,
    change: function() {
      progressLabel.text( progressbar.progressbar( "value" ) + "%" );
    },
    complete: function() {
      progressLabel.text( "Complete" );
    }
  });

  function progress() {
    var template_name = $('#loaded-template-name').html();

    $.post('/extras',{'func':'progress','name':template_name},
      function(data)
      {
        if (data.hasOwnProperty('ecode')) { 
          switch(data.ecode)
          {
            case '300':
              progressbar.progressbar( "value", data.progress);
              var val = progressbar.progressbar( "value" ) || 0;
              if ( val < 99 ) {
                setTimeout( progress, 1000 );
              }
              break;
            case '302':
              progressbar.progressbar( "value", data.progress);
              $( ".progress-label" ).text( "Throttled" );
              break;
            default:
              console.log('Error in progress bar: ' + data.ecode)
          }
        } else {
          console.log('Error in progress bar: ' + data);
        }
      }, "json");
  }

  setTimeout( progress, 5000 );
}

