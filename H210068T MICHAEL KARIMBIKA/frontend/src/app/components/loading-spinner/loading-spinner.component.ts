import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { LoadingService } from '../../services/loading.service';

@Component({
  selector: 'app-loading-spinner',
  imports: [CommonModule],
  templateUrl: './loading-spinner.component.html',
  styleUrl: './loading-spinner.component.css'
})
export class LoadingSpinnerComponent implements 
  OnInit {
    loading = false
  
    constructor(private loadingService: LoadingService) {}
  
    ngOnInit(): void {
      this.loadingService.loading$.subscribe((loading) => {
        this.loading = loading
      })
    }
  }