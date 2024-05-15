function set_slider() {
  $('#jspsych-html-slider-response-response-human').slider();
  $('#jspsych-html-slider-response-response-ai').slider();
    
  // hide all slider handles
  $('.ui-slider-handle').hide();

  $('#jspsych-html-slider-response-response-human').slider().on('slidestart', function( event, ui ) {
      // show handle
      $(this).find('.ui-slider-handle').show();
      // enable buttons if both handles are set
      if ($('.ui-slider-handle:hidden').length == 0) {
        $('#jspsych-html-slider-response-textbox').prop('disabled', false);
        $('#jspsych-html-slider-response-next').prop('disabled', false);
      }
  });

  $('#jspsych-html-slider-response-response-ai').slider().on('slidestart', function( event, ui ) {
      // show handle
      $(this).find('.ui-slider-handle').show();
      // enable buttons if both handles are set
      if ($('.ui-slider-handle:hidden').length == 0) {
        $('#jspsych-html-slider-response-textbox').prop('disabled', false);
        $('#jspsych-html-slider-response-next').prop('disabled', false);
      }
  });
}

function shuffle(array) {
  var currentIndex = array.length, temporaryValue, randomIndex;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}

function range(start, end) {
  // includes start, excludes end
  return new Array(end - start).fill().map((d, i) => i + start);
}

function generate_trial_order(t) {

  var num_of_trials = t.length;
  var trial_order;
  var isValid;

  do {
    isValid = true;
    trial_order = shuffle(range(0, num_of_trials));
    
    // reshuffle if trials with similar factual episodes are placed in consecutive indices
    for (let i = 0; i < trial_order.length; i+=2) {
      if (trial_order.indexOf(i) + 1 === trial_order.indexOf(i+1)) {
        isValid = false;
        break;
      }
      if (trial_order.indexOf(i+1) + 1 === trial_order.indexOf(i)) {
        isValid = false;
        break;
      }
    }
  }
  while (!isValid);

  return trial_order;
}