function selectSection(client, number) {
    let dropdown = `interpretation-singlesample nav select option:nth-child(${number})`;
    return client
        .waitForElementVisible(dropdown)
        .click(dropdown);
}

var commands = {
    'selectSectionFrequency': function() {
        return selectSection(this, 1);
    },
    'selectSectionClassification': function() {
        return selectSection(this, 2);
    },
    'selectSectionReport': function() {
        return selectSection(this, 3);
    },
}

module.exports = {
  commands: [commands],
  url: function() {return this.api.launchUrl + '/analyses'},
  elements: {
    analysis: {
      selector: 'analysis'
    }
  }
};
