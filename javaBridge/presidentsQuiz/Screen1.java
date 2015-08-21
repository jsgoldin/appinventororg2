package com.example.presidentsquiz;
// you need the following imports in all Java Bridge apps
import com.google.appinventor.components.runtime.HandlesEventDispatching;
import com.google.appinventor.components.runtime.EventDispatcher;
import com.google.appinventor.components.runtime.Form;
import com.google.appinventor.components.runtime.Component;

// import the components you'll use
import com.google.appinventor.components.runtime.Button;
import com.google.appinventor.components.runtime.Label;
import com.google.appinventor.components.runtime.Image;
import com.google.appinventor.components.runtime.TextBox;
import com.google.appinventor.components.runtime.HorizontalArrangement;

import java.util.ArrayList;

// the usual Java Bridge Hader
public class Screen1 extends Form implements HandlesEventDispatching
{		
	// declare all your components as variables
	private Label headerLabel;
	private Image image;
	private Label questionLabel;
	private Button nextButton;
	private HorizontalArrangement hArrangement1;
	private TextBox answerTextBox;
	private Button submitButton;
	private Label resultLabel;
	
	private ArrayList<String> questions;
	private ArrayList<String> answers;
	private ArrayList<String> imageFiles;
	private int index=0;
	
	protected void $define()
	{
		questions = new ArrayList<String>();
		questions.add("Which US President created the 'New Deal'?");
		questions.add("Which US President normalized relations between the US and China?");
		
		answers = new ArrayList<String>();
		answers.add("Roosevelt");
		answers.add("Carter");
		
		imageFiles = new ArrayList<String>();
		imageFiles.add("roosChurch.gif");
		imageFiles.add("carterChina.gif");
		
		this.AlignHorizontal(ALIGNMENT_CENTER); // doesn't seem to work
		this.Title("US Presidents Quiz");
		headerLabel = new Label(this);
		headerLabel.FontSize(24);
		headerLabel.Text("Test your knowledge of US Presidents");
		image = new Image(this);  
		image.Width(this.LENGTH_FILL_PARENT);
		image.Picture(imageFiles.get(0));
		
		questionLabel = new Label(this);
		questionLabel.Text(questions.get(0));
		
		nextButton = new Button(this);
		nextButton.Text("Next");
		
		hArrangement1 = new HorizontalArrangement(this);
		hArrangement1.Width(LENGTH_FILL_PARENT);
		answerTextBox = new TextBox (hArrangement1);
		answerTextBox.Width(LENGTH_FILL_PARENT);
		answerTextBox.BackgroundColor(this.COLOR_LTGRAY);
		answerTextBox.Hint("enter answer (last names, all caps)");
		submitButton = new Button(hArrangement1);
		submitButton.Text("Submit");
		resultLabel = new Label(this);
		resultLabel.Text("");
		
		EventDispatcher.registerEventForDelegation( this, "Next", "Click" );
	}
	public boolean dispatchEvent(Component component, String componentName, String eventName, Object[] params )
	{
		// when nextButton.click
		if( component.equals(nextButton) && eventName.equals("Click") ) {
				index = index + 1;
				if (index == questions.size()) {
					index=0;
				}
				questionLabel.Text(questions.get(index));
				image.Picture(imageFiles.get(index));
				// blank our resultLabel and answerTextBox
				resultLabel.Text("");
				answerTextBox.Text("");
				return true;
		} else
		// when submitButton.click
		if( component.equals(submitButton) && eventName.equals("Click") ) {
					if (answerTextBox.Text().equals(answers.get(index))) {
						resultLabel.Text("CORRECT!");
					} else {
						resultLabel.Text("INCORRECT");
					}
					return true;
		} else
		    return false;
	}
	
	
}