///////////////////////////////////////////////////////////////////////////
// C++ code generated with wxFormBuilder (version 3.10.1-0-g8feb16b)
// http://www.wxformbuilder.org/
//
// PLEASE DO *NOT* EDIT THIS FILE!
///////////////////////////////////////////////////////////////////////////

#include "noname.h"

///////////////////////////////////////////////////////////////////////////

jjwxc::jjwxc( wxWindow* parent, wxWindowID id, const wxString& title, const wxPoint& pos, const wxSize& size, long style ) : wxFrame( parent, id, title, pos, size, style )
{
	this->SetSizeHints( wxDefaultSize, wxDefaultSize );

	wxBoxSizer* bSizer1;
	bSizer1 = new wxBoxSizer( wxVERTICAL );

	download_config = new wxNotebook( this, wxID_ANY, wxDefaultPosition, wxDefaultSize, 0 );
	jjwxc = new wxPanel( download_config, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxTAB_TRAVERSAL );
	wxBoxSizer* bSizer4;
	bSizer4 = new wxBoxSizer( wxVERTICAL );

	wxGridBagSizer* gbSizer3;
	gbSizer3 = new wxGridBagSizer( 0, 0 );
	gbSizer3->SetFlexibleDirection( wxBOTH );
	gbSizer3->SetNonFlexibleGrowMode( wxFLEX_GROWMODE_SPECIFIED );

	m_staticText16 = new wxStaticText( jjwxc, wxID_ANY, wxT("Name:"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText16->Wrap( -1 );
	gbSizer3->Add( m_staticText16, wxGBPosition( 0, 0 ), wxGBSpan( 1, 1 ), wxALL, 5 );

	m_textCtrl11 = new wxTextCtrl( jjwxc, wxID_ANY, wxEmptyString, wxDefaultPosition, wxSize( 200,-1 ), 0 );
	gbSizer3->Add( m_textCtrl11, wxGBPosition( 0, 1 ), wxGBSpan( 1, 1 ), wxALIGN_LEFT|wxALL, 5 );

	m_staticText17 = new wxStaticText( jjwxc, wxID_ANY, wxT("Author:"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText17->Wrap( -1 );
	gbSizer3->Add( m_staticText17, wxGBPosition( 0, 2 ), wxGBSpan( 1, 1 ), wxALIGN_RIGHT|wxALL, 5 );

	m_textCtrl12 = new wxTextCtrl( jjwxc, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	gbSizer3->Add( m_textCtrl12, wxGBPosition( 0, 3 ), wxGBSpan( 1, 1 ), wxALIGN_RIGHT|wxALL, 5 );

	m_staticText21 = new wxStaticText( jjwxc, wxID_ANY, wxT("Save to"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText21->Wrap( -1 );
	gbSizer3->Add( m_staticText21, wxGBPosition( 1, 0 ), wxGBSpan( 1, 1 ), wxALL, 5 );

	m_dirPicker1 = new wxDirPickerCtrl( jjwxc, wxID_ANY, wxEmptyString, wxT("Select a folder"), wxDefaultPosition, wxDefaultSize, wxDIRP_DEFAULT_STYLE );
	gbSizer3->Add( m_dirPicker1, wxGBPosition( 1, 1 ), wxGBSpan( 1, 3 ), wxALL|wxEXPAND, 5 );

	m_staticText22 = new wxStaticText( jjwxc, wxID_ANY, wxT("Preface:"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText22->Wrap( -1 );
	gbSizer3->Add( m_staticText22, wxGBPosition( 2, 0 ), wxGBSpan( 1, 1 ), wxALL, 5 );

	m_textCtrl16 = new wxTextCtrl( jjwxc, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_MULTILINE );
	gbSizer3->Add( m_textCtrl16, wxGBPosition( 3, 0 ), wxGBSpan( 7, 4 ), wxALL|wxEXPAND, 5 );


	bSizer4->Add( gbSizer3, 1, wxSHAPED, 5 );

	m_choicebook3 = new wxChoicebook( jjwxc, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxCHB_DEFAULT );
	m_panel8 = new wxPanel( m_choicebook3, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxTAB_TRAVERSAL );
	wxGridBagSizer* gbSizer5;
	gbSizer5 = new wxGridBagSizer( 0, 0 );
	gbSizer5->SetFlexibleDirection( wxBOTH );
	gbSizer5->SetNonFlexibleGrowMode( wxFLEX_GROWMODE_SPECIFIED );

	m_staticText19 = new wxStaticText( m_panel8, wxID_ANY, wxT("Catalogue (URL or novel ID):"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText19->Wrap( -1 );
	m_staticText19->SetToolTip( wxT("Catalogue URL or novel ID") );

	gbSizer5->Add( m_staticText19, wxGBPosition( 0, 0 ), wxGBSpan( 1, 1 ), wxALL, 5 );

	m_textCtrl14 = new wxTextCtrl( m_panel8, wxID_ANY, wxEmptyString, wxDefaultPosition, wxSize( 450,-1 ), 0 );
	gbSizer5->Add( m_textCtrl14, wxGBPosition( 1, 0 ), wxGBSpan( 1, 1 ), wxALL|wxEXPAND, 5 );


	m_panel8->SetSizer( gbSizer5 );
	m_panel8->Layout();
	gbSizer5->Fit( m_panel8 );
	m_choicebook3->AddPage( m_panel8, wxT("From catalogue"), true );
	m_panel9 = new wxPanel( m_choicebook3, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxTAB_TRAVERSAL );
	wxWrapSizer* wSizer2;
	wSizer2 = new wxWrapSizer( wxHORIZONTAL, wxWRAPSIZER_DEFAULT_FLAGS );

	m_staticText23 = new wxStaticText( m_panel9, wxID_ANY, wxT("MyLabel"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText23->Wrap( -1 );
	wSizer2->Add( m_staticText23, 0, wxALL, 5 );

	m_textCtrl17 = new wxTextCtrl( m_panel9, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	wSizer2->Add( m_textCtrl17, 0, wxALL, 5 );


	m_panel9->SetSizer( wSizer2 );
	m_panel9->Layout();
	wSizer2->Fit( m_panel9 );
	m_choicebook3->AddPage( m_panel9, wxT("Chapter by chapter"), false );
	bSizer4->Add( m_choicebook3, 1, wxALL|wxEXPAND, 5 );


	jjwxc->SetSizer( bSizer4 );
	jjwxc->Layout();
	bSizer4->Fit( jjwxc );
	download_config->AddPage( jjwxc, wxT("Green JJWXC"), true );

	bSizer1->Add( download_config, 1, wxEXPAND | wxALL, 5 );


	this->SetSizer( bSizer1 );
	this->Layout();

	this->Centre( wxBOTH );
}

jjwxc::~jjwxc()
{
}
