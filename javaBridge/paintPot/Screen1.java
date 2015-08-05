package com.example.paintpot;

import com.google.appinventor.components.runtime.HandlesEventDispatching;
import com.google.appinventor.components.runtime.Form;
import com.google.appinventor.components.runtime.EventDispatcher;
import com.google.appinventor.components.runtime.Component;

import com.google.appinventor.components.runtime.HorizontalArrangement;
import com.google.appinventor.components.runtime.Button;
import com.google.appinventor.components.runtime.Camera;
import com.google.appinventor.components.runtime.Canvas;

public class Screen1 extends Form implements HandlesEventDispatching
{
	
	private float dotSize;
	
	private Canvas canvas1;
	private HorizontalArrangement horizontalArrangement1;
	private Button redButton;
	private Button blueButton;
	private Button greenButton;
	private Button bigButton;
	private Button smallButton;
	private Button takePictureButton;
	private Camera camera1;
	
	protected void $define()
	{
		this.Title("Paint Pot");
		this.Icon("kitty.png");
		dotSize = 2;
		canvas1 = new Canvas( this );
		canvas1.Height( 300 );
		canvas1.Width(LENGTH_FILL_PARENT);
		canvas1.BackgroundImage( "kitty.png" );
		
		canvas1.PaintColor(COLOR_RED);
		
		horizontalArrangement1 = new HorizontalArrangement( this );
		horizontalArrangement1.Width(LENGTH_FILL_PARENT);
		
		takePictureButton = new Button( this );
		takePictureButton.Text( "Take Picture" );
		
		camera1 = new Camera( this );
		
		redButton = new Button( horizontalArrangement1 );
		redButton.Text( "RED" );
		redButton.TextColor(COLOR_RED );
		
		blueButton = new Button( horizontalArrangement1 );
		blueButton.Text( "BLUE" );
		
		greenButton = new Button( horizontalArrangement1 );
		greenButton.Text( "GREEN" );
		
		bigButton = new Button( horizontalArrangement1 );
		bigButton.Text( "BIG" );
		
		smallButton = new Button( horizontalArrangement1 );
		smallButton.Text( "SMALL" );
		// you can initialize things in $define or in the Initialize event (see below)
		EventDispatcher.registerEventForDelegation( this, "canvas1", "Initialize" );
		EventDispatcher.registerEventForDelegation( this, "canvas1", "Touched" );
		EventDispatcher.registerEventForDelegation( this, "canvas1", "Dragged" );
		EventDispatcher.registerEventForDelegation( this, "buttonClick", "Click" );
		EventDispatcher.registerEventForDelegation( this, "camera1", "AfterPicture" );
	}
	// dispatchEvent handles all events. You'll use an if-else to identify the component and
	// event and you can either call a method or just respond to the event directly 
	// params provides the event parameters, params[0] is first, and so on
	public boolean dispatchEvent( Component component, String componentName, String eventName, Object[] params )
	{   
		if( component.equals(canvas1) && eventName.equals("Touched") )
		{
			    // touched event has two parameters x,y, which are floats (for some reason) and touchedSprite which is a boolean
				//   so params[0] is x, params[1] is y and params[2] is touched sprite
				canvas1Touched((Float) params[0], (Float) params[1], (Boolean) params[2]);
				return true;
		}
		if( component.equals(canvas1) && eventName.equals("Dragged") )
		{
				canvas1Dragged((Float) params[0], (Float) params[1], (Float) params[2], (Float) params[3], (Float) params[4], (Float) params[5], (Boolean) params[6]);
				return true;
		}
		if( component.equals(redButton) && eventName.equals("Click") )
		{
				redButtonClick();
				return true;
		}
		if( component.equals(blueButton) && eventName.equals("Click") )
		{
				blueButtonClick();
				return true;
		}
		if( component.equals(greenButton) && eventName.equals("Click") )
		{
				greenButtonClick();
				return true;
		}
		if( component.equals(bigButton) && eventName.equals("Click") )
		{
				bigButtonClick();
				return true;
		}
		if( component.equals(smallButton) && eventName.equals("Click") )
		{
				smallButtonClick();
				return true;
		}
		if( component.equals(takePictureButton) && eventName.equals("Click") )
		{
				takePictureButtonClick();
				return true;
		}
		if( component.equals(camera1) && eventName.equals("AfterPicture") )
		{
				camera1AfterPicture((String) params[0]);
				return true;
		}
		return false;
	}
	
	public void canvas1Touched( Float x, Float y, Boolean touchedSprite )
	{
		canvas1.DrawCircle( x.intValue(),y.intValue(), dotSize,true );
		
	}
	public void canvas1Dragged( Float startX, Float startY, Float prevX, Float prevY, Float currentX, Float currentY, Boolean draggedSprite )
	{	
		canvas1.DrawLine( prevX.intValue(), prevY.intValue(), currentX.intValue(), currentY.intValue() );
	}
	public void redButtonClick()
	{
		
		canvas1.PaintColor(COLOR_RED);
		redButton.TextColor(COLOR_RED);
		greenButton.TextColor(COLOR_BLACK );
		blueButton.TextColor( COLOR_BLACK );
	}
	public void blueButtonClick()
	{	
		canvas1.PaintColor( COLOR_BLUE );
		blueButton.TextColor( COLOR_BLUE );
		greenButton.TextColor( COLOR_BLACK );
		redButton.TextColor( COLOR_BLACK );
	}
	public void greenButtonClick()
	{	
		canvas1.PaintColor( COLOR_GREEN );
		greenButton.TextColor( COLOR_GREEN );
		blueButton.TextColor( COLOR_BLACK );
		redButton.TextColor( COLOR_BLACK );
	}
	public void bigButtonClick()
	{	
		dotSize = 8;
	}
	public void smallButtonClick()
	{	
		dotSize = 2;
	}
	public void takePictureButtonClick()
	{	
		camera1.TakePicture();
	}
	public void camera1AfterPicture( String image )
	{	
		canvas1.BackgroundImage( image );
	}
}