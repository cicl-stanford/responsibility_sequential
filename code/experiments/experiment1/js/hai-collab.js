/**
 * a jspsych plugin for a 2-slider response question on human-AI collaboration
 *
 */

var jsHAICollab = (function (jspsych) {
  "use strict";

  const info = {
    name: 'hai-collab',
    description: 'Human-AI Collaboration 2-slider response question',
    parameters: {
      trial: {
        type: jspsych.ParameterType.HTML_STRING,
        pretty_name: 'Trial',
        default: null,
        description: 'Trial number'
      },
      prompt_human: {
        type: jspsych.ParameterType.STRING,
        pretty_name: 'Prompt for human',
        default: '',
        description: '',
      },
      prompt_ai: {
        type: jspsych.ParameterType.STRING,
        pretty_name: 'Prompt for AI',
        default: '',
        description: '',
      },
      textbox: {
        type: jspsych.ParameterType.BOOL,
        pretty_name: 'Whether to show a textbox below the sliders',
        default: false,
        description: '',
      }
    }
  };

  var slider_width = 550;
  var slider_labels = ['Not at all', 'Very much'];
  var button_label = 'Continue';

  class HAICollabPlugin {
    constructor(jsPsych) {
      this.jsPsych = jsPsych;
    }
    trial(display_element, trial) {

      var html = '<div id="jspsych-html-slider-response-wrapper">';
      // GIF
      html += '<div id="jspsych-html-slider-response-stimulus"><img style="width: 450px;" src="trials/' + trial.trial + '/episode.gif"></img></div>';
      html += '<div class="jspsych-html-slider-response-container" style="position:relative; margin: 0 auto 2em auto; width:' + slider_width + 'px;">';
      
      // first prompt & slider
      html += '<p style="margin: 0 auto 0 auto;">' + trial.prompt_human + '</p>';
      html += '<div style="width: 100%;" id="jspsych-html-slider-response-response-human"></div>';
      html += '<div>'
      for(var j=0; j < slider_labels.length; j++){
        var width = 100/(slider_labels.length-1);
        var left_offset = (j * (100 /(slider_labels.length - 1))) - (width/2);
        html += '<div style="display: inline-block; position: absolute; left:'+left_offset+'%; text-align: center; width: '+width+'%;">';
        html += '<span style="text-align: center; font-size: 80%;">'+slider_labels[j]+'</span>';
        html += '</div>'
      }
      html += '</div>';

      // second prompt & slider
      html += '<div style="margin: 3em auto 0 auto;">'
      html += '<p style="margin: 0 auto 0 auto;">' + trial.prompt_ai + '</p>';
      html += '<div style="width: 100%;" id="jspsych-html-slider-response-response-ai"></div>';
      html += '<div>'
      for(var j=0; j < slider_labels.length; j++){
        var width = 100/(slider_labels.length-1);
        var left_offset = (j * (100 /(slider_labels.length - 1))) - (width/2);
        html += '<div style="display: inline-block; position: absolute; left:'+left_offset+'%; text-align: center; width: '+width+'%;">';
        html += '<span style="text-align: center; font-size: 80%;">'+slider_labels[j]+'</span>';
        html += '</div>'
      }
      html += '</div>';

      html += '</div>';
      html += '</div>';
      
      // hidden textbox
      html += '<p id="jspsych-html-slider-response-instructions" style="display: none; text-align: center; margin: 0 0;">Briefly explain why you assigned responsibility this way.</p>';
      html += '<textarea id="jspsych-html-slider-response-text" style="display: none; width: 100%; height: 80px; margin: 0 0; resize: none;"></textarea>';

      if (trial.textbox) {
        // add textbox button
        html += '<button id="jspsych-html-slider-response-textbox" class="jspsych-btn" disabled>'+button_label+'</button>';
      }

      // add submit button
      if (trial.textbox) {
        // invisible if the textbox is going to appear
        html += '<button id="jspsych-html-slider-response-next" class="jspsych-btn" style="display: none;" disabled>'+button_label+'</button>';
      } else {
        // visible otherwise
        html += '<button id="jspsych-html-slider-response-next" class="jspsych-btn" disabled>'+button_label+'</button>';
      }
      display_element.innerHTML = html;

      var response = {};

      set_slider();
      
      if (trial.textbox) {
        // event listener for the textbox button
        display_element.querySelector('#jspsych-html-slider-response-textbox').addEventListener('click', function() {
          // disable the sliders
          $('#jspsych-html-slider-response-response-human').slider("option", "disabled", true);
          $('#jspsych-html-slider-response-response-ai').slider("option", "disabled", true);
          // change the color of the disabled sliders
          $('.ui-state-disabled .ui-slider-range').css('background', '#cccccc');
          $('.ui-state-disabled .ui-slider-handle').css('background', '#cccccc');
          // show the textbox
          $('#jspsych-html-slider-response-instructions').show();
          $('#jspsych-html-slider-response-text').show();
          // show the submit button and make it disabled by default
          $('#jspsych-html-slider-response-next').show();
          $('#jspsych-html-slider-response-next').prop('disabled', true);
          // hide the first button
          $('#jspsych-html-slider-response-textbox').hide();
        });

        // event listener for the textbox to check if the user entered anything and make the submit button enabled
        display_element.querySelector('#jspsych-html-slider-response-text').addEventListener('input', function() {
          if (this.value.length > 0) {
            display_element.querySelector('#jspsych-html-slider-response-next').disabled = false;
          } else {
            display_element.querySelector('#jspsych-html-slider-response-next').disabled = true;
          }
        });
      }

      // event listener for the submit button
      display_element.querySelector('#jspsych-html-slider-response-next').addEventListener('click', function() {
        response.human_slider = $('#jspsych-html-slider-response-response-human').slider('option', 'value');
        response.ai_slider = $('#jspsych-html-slider-response-response-ai').slider('option', 'value');
        response.text = $('#jspsych-html-slider-response-text').val();
        end_trial();
      });
      
      // store the timestamp for the start of the trial
      var start_time = jsPsych.getTotalTime();

      function end_trial(){
  
        jsPsych.pluginAPI.clearAllTimeouts();
        
        // get response time
        var end_time = jsPsych.getTotalTime();
        var response_time = end_time - start_time;

        // save data
        var data = {
          "trial": trial.trial,
          "response_human": response.human_slider,
          "response_ai": response.ai_slider,
          "response_text": response.text,
          "rt": response_time
        };
        display_element.innerHTML = '';
  
        // next trial
        jsPsych.finishTrial(data);
      }
    }
  }
  HAICollabPlugin.info = info;

  return HAICollabPlugin;
})(jsPsychModule);