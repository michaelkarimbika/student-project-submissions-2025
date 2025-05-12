import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PaymentReturnComponent } from './payment-return.component';

describe('PaymentReturnComponent', () => {
  let component: PaymentReturnComponent;
  let fixture: ComponentFixture<PaymentReturnComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PaymentReturnComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PaymentReturnComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
